from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from app.asr.base import ASRInferenceError, ASRModelUnavailableError, HealthStatus, TranscriptResult
from app.config import Settings

logger = logging.getLogger(__name__)

WARMUP_SAMPLE_RATE = 16000


class FasterWhisperEngine:
    def __init__(self, settings: Settings) -> None:
        self._model_name = settings.asr_model
        self._backend = settings.asr_backend
        self._device = settings.asr_device
        self._compute_type = settings.asr_compute_type
        self._model = None
        self._ready = False
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="asr")

    async def warmup(self) -> None:
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(self._executor, self._load_model)
            await loop.run_in_executor(self._executor, self._run_warmup_inference)
        except Exception as exc:
            self._ready = False
            raise ASRModelUnavailableError(f"Failed to load ASR model: {exc}") from exc
        self._ready = True
        logger.info("ASR model loaded and warmed up: %s", self._model_name)

    async def health(self) -> HealthStatus:
        return HealthStatus(
            ready=self._ready,
            backend=self._backend,
            model=self._model_name,
            message=None if self._ready else "Model not loaded",
        )

    async def transcribe_partial(
        self,
        audio: bytes,
        segment_id: str,
        language: str,
    ) -> TranscriptResult:
        return await self._transcribe(audio, segment_id, language, partial=True)

    async def transcribe_final(
        self,
        audio: bytes,
        segment_id: str,
        language: str,
    ) -> TranscriptResult:
        return await self._transcribe(audio, segment_id, language, partial=False)

    async def _transcribe(
        self,
        audio: bytes,
        segment_id: str,
        language: str,
        *,
        partial: bool,
    ) -> TranscriptResult:
        if not self._ready or self._model is None:
            raise ASRModelUnavailableError("ASR model is not loaded")

        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(
                self._executor,
                lambda: self._transcribe_sync(audio, language, partial=partial),
            )
        except ASRModelUnavailableError:
            raise
        except Exception as exc:
            raise ASRInferenceError(
                f"ASR inference failed for segment {segment_id}: {exc}"
            ) from exc

    def _load_model(self) -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise ASRModelUnavailableError(
                "faster-whisper is not installed; install with pip install faster-whisper"
            ) from exc

        logger.info("Loading faster-whisper model: %s", self._model_name)
        self._model = WhisperModel(
            self._model_name,
            device=self._device,
            compute_type=self._compute_type,
        )

    def _run_warmup_inference(self) -> None:
        silence = np.zeros(WARMUP_SAMPLE_RATE, dtype=np.float32)
        self._transcribe_array(silence, language="en", partial=False)

    def _transcribe_sync(self, audio: bytes, language: str, *, partial: bool) -> TranscriptResult:
        audio_array = self._pcm_bytes_to_float32(audio)
        return self._transcribe_array(audio_array, language=language, partial=partial)

    def _transcribe_array(
        self,
        audio: np.ndarray,
        *,
        language: str,
        partial: bool,
    ) -> TranscriptResult:
        if self._model is None:
            raise ASRModelUnavailableError("ASR model is not loaded")

        segments, info = self._model.transcribe(
            audio,
            language=language,
            beam_size=1 if partial else 5,
            vad_filter=False,
        )
        text = "".join(segment.text for segment in segments).strip()
        detected_language = info.language or language
        confidence = float(info.language_probability) if info.language_probability is not None else None
        return TranscriptResult(text=text, language=detected_language, confidence=confidence)

    @staticmethod
    def _pcm_bytes_to_float32(pcm_data: bytes) -> np.ndarray:
        audio_int16 = np.frombuffer(pcm_data, dtype=np.int16)
        return audio_int16.astype(np.float32) / 32768.0
