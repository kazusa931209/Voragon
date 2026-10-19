from __future__ import annotations

import base64
import binascii
import time

from fastapi import APIRouter, HTTPException, Request

from app.asr.api_models import AsrInferenceRequest, AsrInferenceResponse
from app.asr.base import ASREngine, ASRInferenceError, ASRModelUnavailableError
from app.asr.inference_metrics import track_inference_queue
from app.observability.metrics import observe_asr_inference_duration, record_asr_inference_error

router = APIRouter(prefix="/v1/inference", tags=["inference"])


@router.post("/asr", response_model=AsrInferenceResponse)
async def inference_asr(body: AsrInferenceRequest, request: Request) -> AsrInferenceResponse:
    """Run partial or final transcription for remote realtime-backend callers (P7-006)."""
    asr_engine: ASREngine = request.app.state.asr_engine
    try:
        audio = base64.b64decode(body.audio_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid audio_base64") from exc

    started = time.perf_counter()
    async with track_inference_queue():
        try:
            if body.kind == "partial":
                result = await asr_engine.transcribe_partial(
                    audio, body.segment_id, body.language
                )
            else:
                result = await asr_engine.transcribe_final(
                    audio, body.segment_id, body.language
                )
        except ASRModelUnavailableError as exc:
            record_asr_inference_error()
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ASRInferenceError as exc:
            record_asr_inference_error()
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        finally:
            observe_asr_inference_duration(time.perf_counter() - started, kind=body.kind)

    return AsrInferenceResponse(
        text=result.text,
        language=result.language,
        confidence=result.confidence,
    )
