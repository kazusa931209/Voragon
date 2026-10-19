import asyncio
import contextlib
import json
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.asr.base import ASREngine, ASRInferenceError, ASRModelUnavailableError
from app.auth.jwt import JwtAuthError, require_realtime_jwt
from app.config import Settings, get_settings
from app.observability.logging_config import log_fields
from app.observability.metrics import (
    observe_asr_inference_duration,
    record_audio_frame,
    record_transcript_final,
    record_transcript_partial,
)
from app.pipeline.audio_buffer import BufferedAudioFrame
from app.pipeline.audio_sequence import SequenceGap, SequenceProcessResult
from app.pipeline.vad import SegmentClosed, SegmentOpened, VadError
from app.websocket.audio_frame import AudioFrameError, parse_audio_frame
from app.websocket.connection_registry import RegisteredConnection, register, unregister
from app.websocket.buffer_overflow import emit_buffer_overflow_notifications
from app.websocket.errors import WebSocketErrorEmitter
from app.websocket.messages import (
    pong,
    session_ended,
    session_started,
    transcript_final,
    transcript_partial,
)
from app.websocket.session import AudioConfig, Session
from app.websocket.session_registry import (
    claim_detached,
    detach_session,
    restore_session,
)

logger = logging.getLogger(__name__)

router = APIRouter()

SUPPORTED_SAMPLE_FORMATS = {"s16le"}


@dataclass
class RealtimeConnection:
    session: Session
    session_id: str
    resumed: bool = False
    errors: WebSocketErrorEmitter | None = None


@router.websocket("/v1/realtime")
async def realtime_websocket(websocket: WebSocket) -> None:
    settings = get_settings()
    if settings.jwt_auth_required:
        secret = settings.jwt_secret
        if not secret:
            logger.error("websocket.auth_misconfigured", extra={"reason": "JWT_SECRET missing"})
            await websocket.close(code=1011, reason="Auth misconfigured")
            return
        try:
            await require_realtime_jwt(
                websocket,
                secret=secret,
                audience=settings.jwt_audience,
            )
        except JwtAuthError:
            log_fields(
                logger,
                logging.INFO,
                "websocket.auth_rejected",
                reason="invalid_or_missing_token",
            )
            await websocket.close(code=4401, reason="Unauthorized")
            return
    await websocket.accept()

    conn = RealtimeConnection(
        session=Session.create(),
        session_id="",
    )
    conn.session_id = str(conn.session.session_id)

    await websocket.send_json(
        session_started(conn.session_id, settings.reconnect_window_s)
    )
    log_fields(
        logger,
        logging.INFO,
        "websocket.connected",
        session_id=conn.session_id,
    )

    activity = asyncio.Event()
    activity.set()
    session_closed = False
    intentional_session_end = False

    def mark_intentional_session_end() -> None:
        nonlocal intentional_session_end
        intentional_session_end = True

    async def end_session(reason: str) -> None:
        nonlocal session_closed, intentional_session_end
        if session_closed:
            return
        if reason in ("timeout", "server_shutdown", "error"):
            intentional_session_end = True
        session_closed = True
        if not watchdog.done():
            watchdog.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await watchdog
        try:
            await websocket.send_json(session_ended(conn.session_id, reason))
            log_fields(
                logger,
                logging.INFO,
                "session.ended",
                session_id=conn.session_id,
                reason=reason,
            )
        except Exception:
            logger.debug(
                "session.ended not delivered session_id=%s reason=%s",
                conn.session_id,
                reason,
            )
        with contextlib.suppress(Exception):
            await websocket.close(code=1000)

    async def idle_watchdog() -> None:
        timeout = settings.heartbeat_idle_timeout_s
        while True:
            try:
                await asyncio.wait_for(activity.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                logger.debug(
                    "heartbeat idle timeout session_id=%s timeout_s=%s",
                    conn.session_id,
                    timeout,
                )
                await end_session("timeout")
                return
            activity.clear()

    watchdog = asyncio.create_task(idle_watchdog())
    conn.errors = WebSocketErrorEmitter(
        websocket,
        conn.session_id,
        end_session,
        max_errors_per_second=settings.error_max_per_second,
    )
    errors = conn.errors
    registered = RegisteredConnection(conn.session_id, end_session)
    await register(registered)

    reorder_flush_task: asyncio.Task[None] | None = None

    async def cancel_reorder_flush() -> None:
        nonlocal reorder_flush_task
        if reorder_flush_task is not None and not reorder_flush_task.done():
            reorder_flush_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await reorder_flush_task
        reorder_flush_task = None

    async def deliver_sequenced(result: SequenceProcessResult) -> None:
        await _emit_sequence_gaps(errors, result.gaps)
        await _deliver_sequenced_frames(
            websocket, conn, settings, result.ready
        )

    async def flush_reorder_buffer(*, force: bool = False) -> None:
        result = conn.session.flush_sequenced_frames(time.monotonic(), force=force)
        await deliver_sequenced(result)
        if (
            not force
            and conn.session.audio_sequence is not None
            and conn.session.audio_sequence.waiting_for_reorder
        ):
            await schedule_reorder_flush()
        else:
            await cancel_reorder_flush()

    async def schedule_reorder_flush() -> None:
        nonlocal reorder_flush_task
        if conn.session.audio_sequence is None:
            await cancel_reorder_flush()
            return
        deadline = conn.session.audio_sequence.flush_deadline()
        if deadline is None:
            await cancel_reorder_flush()
            return
        delay = max(0.0, deadline - time.monotonic())
        await cancel_reorder_flush()

        async def wait_and_flush() -> None:
            await asyncio.sleep(delay)
            await flush_reorder_buffer(force=False)

        reorder_flush_task = asyncio.create_task(wait_and_flush())

    try:
        while not session_closed:
            message = await websocket.receive()
            activity.set()

            if message.get("type") == "websocket.disconnect":
                break

            try:
                if "text" in message:
                    await _handle_text_message(
                        conn,
                        message["text"],
                        settings,
                        end_session,
                        flush_reorder_buffer,
                        mark_intentional_session_end,
                    )
                elif "bytes" in message:
                    await _handle_binary_message(
                        websocket,
                        conn,
                        message["bytes"],
                        settings,
                        deliver_sequenced,
                        schedule_reorder_flush,
                    )
            except Exception:
                logger.exception(
                    "Unexpected error handling message session_id=%s",
                    conn.session_id,
                )
                await errors.emit(
                    "INTERNAL_ERROR",
                    "Unexpected server error",
                    recoverable=False,
                )
            if session_closed:
                break
    except WebSocketDisconnect:
        log_fields(
            logger,
            logging.INFO,
            "websocket.disconnected",
            session_id=conn.session_id,
        )
    finally:
        await cancel_reorder_flush()
        await unregister(registered)
        if not watchdog.done():
            watchdog.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await watchdog
        if (
            not intentional_session_end
            and conn.session.audio_started
        ):
            await detach_session(conn.session, settings.reconnect_window_s)
            logger.debug(
                "session detached for reconnect window session_id=%s window_s=%s",
                conn.session_id,
                settings.reconnect_window_s,
            )
        if not session_closed:
            await end_session("client_stop")


def _connection_errors(conn: RealtimeConnection) -> WebSocketErrorEmitter:
    assert conn.errors is not None
    return conn.errors


async def _handle_text_message(
    conn: RealtimeConnection,
    text: str,
    settings: Settings,
    end_session: Callable[[str], Awaitable[None]],
    flush_reorder_buffer: Callable[..., Awaitable[None]],
    mark_intentional_session_end: Callable[[], None],
) -> None:
    errors = _connection_errors(conn)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        await errors.emit("INVALID_MESSAGE", "Malformed message")
        return

    if not isinstance(data, dict):
        await errors.emit("INVALID_MESSAGE", "Message must be a JSON object")
        return

    message_type = data.get("type")
    if not isinstance(message_type, str) or not message_type:
        await errors.emit("INVALID_MESSAGE", "Missing or invalid message type")
        return

    if message_type == "audio.start":
        await _handle_audio_start(conn, data, settings)
        return
    if message_type == "audio.stop":
        await _handle_audio_stop(
            conn,
            data,
            settings,
            end_session,
            flush_reorder_buffer,
            mark_intentional_session_end,
        )
        return
    if message_type == "ping":
        await _handle_ping(conn, data)
        return
    if message_type == "session.resume":
        await _handle_session_resume(conn, data, settings)
        return

    await errors.emit(
        "UNKNOWN_MESSAGE_TYPE",
        f"Unrecognized message type: {message_type}",
    )


async def _handle_session_resume(
    conn: RealtimeConnection,
    data: dict[str, Any],
    settings: Settings,
) -> None:
    errors = _connection_errors(conn)
    websocket = errors.websocket
    envelope_error = _validate_session_resume_envelope(data)
    if envelope_error is not None:
        await errors.emit("INVALID_MESSAGE", envelope_error)
        return

    if conn.resumed:
        await errors.emit(
            "INVALID_MESSAGE",
            "Session already restored on this connection",
        )
        return

    if conn.session.audio_started:
        await errors.emit(
            "INVALID_MESSAGE",
            "Cannot resume after audio.start on interim session",
        )
        return

    previous_session_id = data.get("session_id")
    assert isinstance(previous_session_id, str)
    try:
        UUID(previous_session_id)
    except ValueError:
        await errors.emit("INVALID_MESSAGE", "session_id must be a valid UUID")
        return

    record, error_code = await claim_detached(previous_session_id)
    if error_code is not None:
        message = (
            "Session not found"
            if error_code == "SESSION_NOT_FOUND"
            else "Session reconnect window expired"
        )
        await errors.emit(error_code, message)
        return

    conn.session = restore_session(
        record, settings, settings.audio_buffer_seconds
    )
    conn.session_id = str(conn.session.session_id)
    conn.resumed = True
    errors.update_session_id(conn.session_id)

    await websocket.send_json(
        session_started(conn.session_id, settings.reconnect_window_s)
    )
    log_fields(
        logger,
        logging.INFO,
        "session.resumed",
        session_id=conn.session_id,
    )


def _validate_session_resume_envelope(data: dict[str, Any]) -> str | None:
    if not isinstance(data.get("id"), str) or not data.get("id"):
        return "Missing or invalid message id"
    if not isinstance(data.get("timestamp"), str) or not data.get("timestamp"):
        return "Missing or invalid timestamp"
    payload = data.get("payload")
    if payload is None:
        return "Missing payload"
    if not isinstance(payload, dict):
        return "payload must be an object"
    previous_id = data.get("session_id")
    if not isinstance(previous_id, str) or not previous_id:
        return "Missing or invalid session_id"
    return None


async def _handle_ping(
    conn: RealtimeConnection,
    data: dict[str, Any],
) -> None:
    errors = _connection_errors(conn)
    session_id = conn.session_id
    envelope_error = _validate_client_envelope(session_id, data)
    if envelope_error is not None:
        await errors.emit("INVALID_MESSAGE", envelope_error)
        return

    payload = data.get("payload")
    if payload is not None and not isinstance(payload, dict):
        await errors.emit("INVALID_MESSAGE", "ping payload must be an object")
        return

    await errors.websocket.send_json(pong(session_id))


def _validate_client_envelope(session_id: str, data: dict[str, Any]) -> str | None:
    if data.get("session_id") != session_id:
        return "session_id does not match active session"
    return None


async def _handle_audio_start(
    conn: RealtimeConnection,
    data: dict[str, Any],
    settings: Settings,
) -> None:
    errors = _connection_errors(conn)
    session = conn.session
    session_id = conn.session_id
    if data.get("session_id") != session_id:
        await errors.emit(
            "INVALID_MESSAGE",
            "session_id does not match active session",
        )
        return

    payload = data.get("payload")
    if payload is not None and not isinstance(payload, dict):
        await errors.emit("INVALID_MESSAGE", "audio.start payload must be an object")
        return

    config, parse_error = _parse_audio_start_payload(payload or {})
    if parse_error is not None:
        await errors.emit("INVALID_MESSAGE", parse_error)
        return

    validation_error = _validate_audio_config(config)
    if validation_error is not None:
        await errors.emit("INVALID_AUDIO_FORMAT", validation_error)
        return

    session.start_audio(config, settings.audio_buffer_seconds, settings)
    logger.debug(
        "Audio started session_id=%s sample_rate=%s channels=%s",
        session_id,
        config.sample_rate,
        config.channels,
    )


async def _handle_audio_stop(
    conn: RealtimeConnection,
    data: dict[str, Any],
    settings: Settings,
    end_session: Callable[[str], Awaitable[None]],
    flush_reorder_buffer: Callable[..., Awaitable[None]],
    mark_intentional_session_end: Callable[[], None],
) -> None:
    errors = _connection_errors(conn)
    websocket = errors.websocket
    session = conn.session
    session_id = conn.session_id
    if data.get("session_id") != session_id:
        await errors.emit(
            "INVALID_MESSAGE",
            "session_id does not match active session",
        )
        return

    if not session.audio_started:
        await errors.emit(
            "AUDIO_NOT_STARTED",
            "Send audio.start before audio.stop",
        )
        return

    asr_engine: ASREngine = websocket.app.state.asr_engine
    await flush_reorder_buffer(force=True)
    await _flush_open_segments(conn, settings, asr_engine)
    logger.debug("Audio stopped session_id=%s", session_id)
    mark_intentional_session_end()
    await end_session("client_stop")


async def _flush_open_segments(
    conn: RealtimeConnection,
    settings: Settings,
    asr_engine: ASREngine,
) -> None:
    session = conn.session
    session_id = conn.session_id
    if session.vad_stream is None:
        return

    loop = asyncio.get_running_loop()
    flush = getattr(session.vad_stream, "flush_active_segment", None)
    if flush is None:
        tracker = getattr(session.vad_stream, "tracker", None)
        if tracker is None:
            return
        events = await loop.run_in_executor(None, tracker.flush_active_segment)
    else:
        events = await loop.run_in_executor(None, flush)

    for event in events:
        if isinstance(event, SegmentClosed):
            logger.debug(
                "segment_flushed session_id=%s segment_id=%s duration_ms=%s",
                session_id,
                event.segment_id,
                event.duration_ms,
            )
            await _emit_transcript_final(
                conn,
                str(event.segment_id),
                event.pcm_data,
                settings,
                asr_engine,
            )


def _parse_audio_start_payload(payload: dict[str, Any]) -> tuple[AudioConfig | None, str | None]:
    language, error = _parse_string_field(payload, "language", "en")
    if error:
        return None, error
    model, error = _parse_string_field(payload, "model", "asr.default")
    if error:
        return None, error
    sample_format, error = _parse_string_field(payload, "sample_format", "s16le")
    if error:
        return None, error
    sample_rate, error = _parse_int_field(payload, "sample_rate", 16000)
    if error:
        return None, error
    channels, error = _parse_int_field(payload, "channels", 1)
    if error:
        return None, error
    frame_duration_ms, error = _parse_int_field(payload, "frame_duration_ms", 20)
    if error:
        return None, error

    return (
        AudioConfig(
            language=language,
            model=model,
            sample_rate=sample_rate,
            channels=channels,
            sample_format=sample_format,
            frame_duration_ms=frame_duration_ms,
        ),
        None,
    )


def _parse_string_field(
    payload: dict[str, Any], field_name: str, default: str
) -> tuple[str, str | None]:
    if field_name not in payload:
        return default, None
    value = payload[field_name]
    if not isinstance(value, str):
        return default, f"{field_name} must be a string"
    return value, None


def _parse_int_field(
    payload: dict[str, Any], field_name: str, default: int
) -> tuple[int, str | None]:
    if field_name not in payload:
        return default, None
    value = payload[field_name]
    if isinstance(value, bool) or not isinstance(value, int):
        return default, f"{field_name} must be an integer"
    return value, None


def _validate_audio_config(config: AudioConfig) -> str | None:
    if config.sample_rate <= 0:
        return "sample_rate must be positive"
    if config.channels != 1:
        return "only mono audio is supported"
    if config.sample_format not in SUPPORTED_SAMPLE_FORMATS:
        return f"unsupported sample_format: {config.sample_format}"
    if config.frame_duration_ms <= 0:
        return "frame_duration_ms must be positive"
    if config.expected_frame_bytes() <= 0:
        return "invalid audio frame configuration"
    return None


async def _handle_binary_message(
    websocket: WebSocket,
    conn: RealtimeConnection,
    data: bytes,
    settings: Settings,
    deliver_sequenced: Callable[[SequenceProcessResult], Awaitable[None]],
    schedule_reorder_flush: Callable[[], Awaitable[None]],
) -> None:
    errors = _connection_errors(conn)
    session = conn.session
    session_id = conn.session_id
    if not session.audio_started or session.audio_config is None:
        await errors.emit(
            "AUDIO_NOT_STARTED",
            "Send audio.start before streaming audio frames",
        )
        return

    try:
        frame = parse_audio_frame(data, session.audio_config)
    except AudioFrameError as exc:
        await errors.emit("INVALID_AUDIO_FORMAT", exc.message)
        return

    buffered = BufferedAudioFrame(
        seq_num=frame.seq_num,
        timestamp_us=frame.timestamp_us,
        pcm_data=frame.pcm_data,
    )
    result = session.ingest_sequenced_frame(buffered, time.monotonic())
    await deliver_sequenced(result)
    if session.audio_sequence is not None and session.audio_sequence.waiting_for_reorder:
        await schedule_reorder_flush()


async def _emit_sequence_gaps(
    errors: WebSocketErrorEmitter,
    gaps: list[SequenceGap],
) -> None:
    for gap in gaps:
        if gap.first_missing == gap.last_missing:
            detail = f"Missing audio frame sequence number {gap.first_missing}"
        else:
            detail = (
                "Missing audio frame sequence numbers "
                f"{gap.first_missing}-{gap.last_missing}"
            )
        await errors.emit("AUDIO_SEQUENCE_GAP", detail)


async def _deliver_sequenced_frames(
    websocket: WebSocket,
    conn: RealtimeConnection,
    settings: Settings,
    frames: list[BufferedAudioFrame],
) -> None:
    for frame in frames:
        await _deliver_audio_frame(websocket, conn, frame, settings)


async def _deliver_audio_frame(
    websocket: WebSocket,
    conn: RealtimeConnection,
    frame: BufferedAudioFrame,
    settings: Settings,
) -> None:
    session = conn.session
    session_id = conn.session_id
    errors = _connection_errors(conn)
    dropped = session.append_audio_frame(frame)
    record_audio_frame(dropped=dropped)
    if dropped and session.buffer_overflow_notifier is not None:
        await emit_buffer_overflow_notifications(
            websocket,
            session_id,
            dropped,
            session.buffer_overflow_notifier,
            errors,
        )

    if session.audio_config is None:
        return

    session.advance_elapsed_ms(session.audio_config.frame_duration_ms)
    asr_engine: ASREngine = websocket.app.state.asr_engine
    await _process_vad_frame(
        conn, frame.pcm_data, settings, asr_engine
    )
    session.release_processed_audio_frame()


async def _process_vad_frame(
    conn: RealtimeConnection,
    pcm_data: bytes,
    settings: Settings,
    asr_engine: ASREngine,
) -> None:
    session = conn.session
    session_id = conn.session_id
    errors = _connection_errors(conn)
    if session.vad_stream is None or session.audio_config is None:
        return

    loop = asyncio.get_running_loop()

    try:
        if session.vad_degraded:
            events = await loop.run_in_executor(
                None, session.vad_stream.process_degraded_frame, pcm_data
            )
        else:
            events = await loop.run_in_executor(
                None, session.vad_stream.process_frame, pcm_data
            )
    except VadError as exc:
        logger.warning(
            "VAD failed session_id=%s error=%s",
            session_id,
            exc,
        )
        session.vad_degraded = True
        session.vad_stream.enter_degraded_mode()
        if not session.vad_error_sent:
            await errors.emit(
                "VAD_FAILED",
                "VAD processing failed; continuing in degraded mode",
            )
            session.vad_error_sent = True
        events = await loop.run_in_executor(
            None, session.vad_stream.process_degraded_frame, pcm_data
        )

    segment_closed_this_frame = False
    for event in events:
        if isinstance(event, SegmentOpened):
            logger.debug(
                "segment_opened session_id=%s segment_id=%s",
                session_id,
                event.segment_id,
            )
            session.begin_segment_asr(str(event.segment_id), session.session_elapsed_ms)
        elif isinstance(event, SegmentClosed):
            logger.debug(
                "segment_closed session_id=%s segment_id=%s duration_ms=%s",
                session_id,
                event.segment_id,
                event.duration_ms,
            )
            segment_closed_this_frame = True
            await _emit_transcript_final(
                conn,
                str(event.segment_id),
                event.pcm_data,
                settings,
                asr_engine,
            )

    if segment_closed_this_frame or session.segment_asr is None:
        return

    if session.should_emit_partial(settings.asr_partial_interval_ms):
        await _emit_transcript_partial(conn, settings, asr_engine)


def _get_active_segment_pcm(session: Session) -> bytes | None:
    if session.vad_stream is None:
        return None
    tracker = getattr(session.vad_stream, "tracker", None)
    if tracker is None or tracker.active_segment is None:
        return None
    return bytes(tracker.active_segment.pcm_data)


async def _emit_transcript_partial(
    conn: RealtimeConnection,
    settings: Settings,
    asr_engine: ASREngine,
) -> None:
    session = conn.session
    session_id = conn.session_id
    errors = _connection_errors(conn)
    if session.segment_asr is None or session.audio_config is None:
        return

    pcm_data = _get_active_segment_pcm(session)
    if not pcm_data:
        return

    segment_id = session.segment_asr.segment_id
    language = session.audio_config.language

    asr_started = time.perf_counter()
    try:
        result = await asr_engine.transcribe_partial(pcm_data, segment_id, language)
    except ASRModelUnavailableError as exc:
        logger.warning(
            "ASR model unavailable session_id=%s error=%s",
            session_id,
            exc,
        )
        await errors.emit(
            "ASR_MODEL_UNAVAILABLE",
            "ASR model is not loaded or unhealthy",
        )
        return
    except ASRInferenceError as exc:
        logger.warning(
            "ASR partial failed session_id=%s segment_id=%s error=%s",
            session_id,
            segment_id,
            exc,
        )
        await errors.emit(
            "ASR_INFERENCE_FAILED",
            f"ASR inference failed for segment {segment_id}",
        )
        session.clear_segment_asr()
        return
    finally:
        observe_asr_inference_duration(
            time.perf_counter() - asr_started,
            kind="partial",
        )

    session.mark_partial_emitted()
    if not result.text:
        return

    sequence = session.next_sequence()
    await errors.websocket.send_json(
        transcript_partial(
            session_id,
            segment_id,
            sequence,
            result.text,
            result.language,
            result.confidence,
        )
    )
    record_transcript_partial()


async def _emit_transcript_final(
    conn: RealtimeConnection,
    segment_id: str,
    pcm_data: bytes,
    settings: Settings,
    asr_engine: ASREngine,
) -> None:
    session = conn.session
    session_id = conn.session_id
    errors = _connection_errors(conn)
    if session.audio_config is None:
        return

    segment_asr = session.segment_asr
    start_ms = segment_asr.start_ms if segment_asr is not None else session.session_elapsed_ms
    end_ms = session.session_elapsed_ms
    language = session.audio_config.language

    asr_started = time.perf_counter()
    try:
        result = await asr_engine.transcribe_final(pcm_data, segment_id, language)
    except ASRModelUnavailableError as exc:
        logger.warning(
            "ASR model unavailable session_id=%s error=%s",
            session_id,
            exc,
        )
        await errors.emit(
            "ASR_MODEL_UNAVAILABLE",
            "ASR model is not loaded or unhealthy",
        )
        return
    except ASRInferenceError as exc:
        logger.warning(
            "ASR final failed session_id=%s segment_id=%s error=%s",
            session_id,
            segment_id,
            exc,
        )
        await errors.emit(
            "ASR_INFERENCE_FAILED",
            f"ASR inference failed for segment {segment_id}",
        )
        session.clear_segment_asr()
        return
    finally:
        observe_asr_inference_duration(
            time.perf_counter() - asr_started,
            kind="final",
        )

    if not result.text:
        session.clear_segment_asr()
        return

    sequence = segment_asr.sequence + 1 if segment_asr is not None else 1
    session.clear_segment_asr()

    await errors.websocket.send_json(
        transcript_final(
            session_id,
            segment_id,
            sequence,
            result.text,
            result.language,
            start_ms,
            end_ms,
            result.confidence,
        )
    )
    record_transcript_final()
