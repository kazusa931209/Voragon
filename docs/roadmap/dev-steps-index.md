# Dev-Steps Index

Registry of all dev-steps. **One dev-step = one commit** (a PR may include multiple dev-step commits). Do not start the next step until the current dev-step is **done**.

**Workflow:** [Dev-Step Template](dev-step-template.md) · Cursor rule: `.cursor/rules/dev-workflow.mdc`

## Status Legend

| Status | Meaning |
|--------|---------|
| `planned` | Defined in markdown; not started |
| `in-progress` | Implementation underway; PR open or pending |
| `done` | Dev-step commit landed; completion recorded (optional PR link) |

## Active Step

**P8-008** — [EKS AI Gateway manifests](dev-step-p8-008-eks-ai-gateway-manifests.md) (`in-progress`).

---

## Phase 1: Local Single-User ASR Prototype

| ID | Title | Status | PR | Doc |
|----|-------|--------|-----|-----|
| P1-001 | Backend scaffold and health endpoint | done | [#2](https://github.com/kazusa931209-cmd/Voragon/pull/2) | [dev-step-p1-001-backend-scaffold.md](dev-step-p1-001-backend-scaffold.md) |
| P1-002 | WebSocket connect and `session.started` | done | [#3](https://github.com/kazusa931209-cmd/Voragon/pull/3) | [dev-step-p1-002-websocket-session-started.md](dev-step-p1-002-websocket-session-started.md) |
| P1-003 | `audio.start` and binary `audio.chunk` reception | done | [#4](https://github.com/kazusa931209-cmd/Voragon/pull/4) | [dev-step-p1-003-audio-start-chunk.md](dev-step-p1-003-audio-start-chunk.md) |
| P1-004 | VAD integration (Silero) | done | [#5](https://github.com/kazusa931209-cmd/Voragon/pull/5) | [dev-step-p1-004-vad-integration.md](dev-step-p1-004-vad-integration.md) |
| P1-005 | ASR adapter and model load | done | [#6](https://github.com/kazusa931209-cmd/Voragon/pull/6) | [dev-step-p1-005-asr-adapter.md](dev-step-p1-005-asr-adapter.md) |
| P1-006 | `transcript.partial` and `transcript.final` | done | [#7](https://github.com/kazusa931209-cmd/Voragon/pull/7) | [dev-step-p1-006-transcript-partial-final.md](dev-step-p1-006-transcript-partial-final.md) |
| P1-007 | Minimal test client (mic → transcript) | done | [#8](https://github.com/kazusa931209-cmd/Voragon/pull/8) | [dev-step-p1-007-minimal-test-client.md](dev-step-p1-007-minimal-test-client.md) |

**Phase 1 exit:** Speak into microphone via test client; receive partial and final English transcripts.

---

## Phase 2: Realtime Production-Like Backend

| ID | Title | Status | PR | Doc |
|----|-------|--------|-----|-----|
| P2-001 | `ping` / `pong` heartbeat | done | [#9](https://github.com/kazusa931209-cmd/Voragon/pull/9) | [dev-step-p2-001-ping-pong-heartbeat.md](dev-step-p2-001-ping-pong-heartbeat.md) |
| P2-002 | `session.ended` lifecycle | done | [#10](https://github.com/kazusa931209-cmd/Voragon/pull/10) | [dev-step-p2-002-session-ended.md](dev-step-p2-002-session-ended.md) |
| P2-003 | Audio frame `seq_num` ordering | done | [#11](https://github.com/kazusa931209-cmd/Voragon/pull/11) | [dev-step-p2-003-audio-seq-ordering.md](dev-step-p2-003-audio-seq-ordering.md) |
| P2-004 | `buffer.overflow` and `BUFFER_OVERFLOW` | done | [#12](https://github.com/kazusa931209-cmd/Voragon/pull/12) | [dev-step-p2-004-buffer-overflow.md](dev-step-p2-004-buffer-overflow.md) |
| P2-005 | Session registry and reconnect window | done | [`dev` @ `6d92099`](https://github.com/kazusa931209-cmd/Voragon/commit/6d92099) | [dev-step-p2-005-session-registry-reconnect-window.md](dev-step-p2-005-session-registry-reconnect-window.md) |
| P2-006 | `session.resume` reconnection | done | [`dev` @ `bc0fcb1`](https://github.com/kazusa931209-cmd/Voragon/commit/bc0fcb1) | [dev-step-p2-006-session-resume.md](dev-step-p2-006-session-resume.md) |
| P2-007 | API error handling alignment | done | [`feat/steps-P2-007-008-009` @ `a976b18`](https://github.com/kazusa931209-cmd/Voragon/commit/a976b18) | [dev-step-p2-007-api-error-handling.md](dev-step-p2-007-api-error-handling.md) |
| P2-008 | Prometheus `/metrics` | done | [`feat/steps-P2-007-008-009` @ `94d0880`](https://github.com/kazusa931209-cmd/Voragon/commit/94d0880) | [dev-step-p2-008-prometheus-metrics.md](dev-step-p2-008-prometheus-metrics.md) |
| P2-009 | Structured JSON logging | done | [`feat/steps-P2-007-008-009` @ `29c905f`](https://github.com/kazusa931209-cmd/Voragon/commit/29c905f) | [dev-step-p2-009-structured-json-logging.md](dev-step-p2-009-structured-json-logging.md) |

**Phase 2 exit:** Reconnect within window; `/metrics` live; errors match API spec; tests pass. See [phases.md](phases.md).

---

## Phase 3: Tauri Desktop Application

| ID | Title | Status | PR | Doc |
|----|-------|--------|-----|-----|
| P3-001 | Tauri 2 + React + TypeScript scaffold | done | [#14](https://github.com/kazusa931209-cmd/Voragon/pull/14) | [dev-step-p3-001-tauri-scaffold.md](dev-step-p3-001-tauri-scaffold.md) |
| P3-002 | WebSocket client (connect + control messages) | done | [#14](https://github.com/kazusa931209-cmd/Voragon/pull/14) | [dev-step-p3-002-websocket-client.md](dev-step-p3-002-websocket-client.md) |
| P3-003 | Transcript UI and client state | done | [#14](https://github.com/kazusa931209-cmd/Voragon/pull/14) | [dev-step-p3-003-transcript-ui.md](dev-step-p3-003-transcript-ui.md) |
| P3-004 | Rust audio capture + IPC | done | [#14](https://github.com/kazusa931209-cmd/Voragon/pull/14) | [dev-step-p3-004-rust-audio-capture.md](dev-step-p3-004-rust-audio-capture.md) |
| P3-005 | End-to-end mic → backend → transcript UI | done | [#14](https://github.com/kazusa931209-cmd/Voragon/pull/14) | [dev-step-p3-005-e2e-streaming.md](dev-step-p3-005-e2e-streaming.md) |
| P3-006 | Settings and connection chrome | done | [#14](https://github.com/kazusa931209-cmd/Voragon/pull/14) | [dev-step-p3-006-settings.md](dev-step-p3-006-settings.md) |
| P3-007 | Client heartbeat and session lifecycle | done | [#14](https://github.com/kazusa931209-cmd/Voragon/pull/14) | [dev-step-p3-007-heartbeat.md](dev-step-p3-007-heartbeat.md) |
| P3-008 | `session.resume` reconnection | done | [#14](https://github.com/kazusa931209-cmd/Voragon/pull/14) | [dev-step-p3-008-session-resume.md](dev-step-p3-008-session-resume.md) |
| P3-009 | System tray + global shortcuts | done | [#14](https://github.com/kazusa931209-cmd/Voragon/pull/14) | [dev-step-p3-009-tray-shortcuts.md](dev-step-p3-009-tray-shortcuts.md) |
| P3-010 | Transcription stats + reconnect stability | done | [#15](https://github.com/kazusa931209-cmd/Voragon/pull/15) | [dev-step-p3-010-desktop-ui-reconnect.md](dev-step-p3-010-desktop-ui-reconnect.md) |

**Phase 3 exit:** [dev-step-phase3-exit.md](dev-step-phase3-exit.md) — manual macOS (required) and Windows (smoke) checklist. See [phases.md](phases.md).

**Suggested order:** P3-001 → P3-002 → P3-003 → P3-004 → P3-005 → P3-006 → P3-007 → P3-008 → P3-009.

---

## Phase 4: Local Docker Compose

| ID | Title | Status | PR | Doc |
|----|-------|--------|-----|-----|
| P4-001 | Realtime backend Dockerfile | done | [`6d3c0c2`](https://github.com/kazusa931209-cmd/Voragon/commit/6d3c0c2) | [dev-step-p4-001-backend-dockerfile.md](dev-step-p4-001-backend-dockerfile.md) |
| P4-002 | Docker Compose (realtime backend) | done | [`821f7cc`](https://github.com/kazusa931209-cmd/Voragon/commit/821f7cc) | [dev-step-p4-002-docker-compose.md](dev-step-p4-002-docker-compose.md) |
| P4-003 | Model weight volume caching | done | [`981b2cc`](https://github.com/kazusa931209-cmd/Voragon/commit/981b2cc) | [dev-step-p4-003-model-cache-volumes.md](dev-step-p4-003-model-cache-volumes.md) |
| P4-004 | Docker dev docs and Phase 4 exit | done | [`6cdd5ef`](https://github.com/kazusa931209-cmd/Voragon/commit/6cdd5ef) | [dev-step-p4-004-docker-dev-docs.md](dev-step-p4-004-docker-dev-docs.md) |

**Suggested order:** P4-001 → P4-002 → P4-003 → P4-004.

**Phase 4 exit:** signed off 2026-10-15 — [dev-step-phase4-exit.md](dev-step-phase4-exit.md). Dev-steps [P4-001](dev-step-p4-001-backend-dockerfile.md)–[P4-004](dev-step-p4-004-docker-dev-docs.md) done.

---

## Phase 5: Local Kubernetes (Kind)

| ID | Title | Status | PR | Doc |
|----|-------|--------|-----|-----|
| P5-001 | Kind cluster and image load | done | [#17](https://github.com/kazusa931209-cmd/Voragon/pull/17) | [dev-step-p5-001-kind-cluster.md](dev-step-p5-001-kind-cluster.md) |
| P5-002 | Local Kubernetes manifests | done | [#17](https://github.com/kazusa931209-cmd/Voragon/pull/17) | [dev-step-p5-002-local-manifests.md](dev-step-p5-002-local-manifests.md) |
| P5-003 | Model cache PVC on Kind | done | [#17](https://github.com/kazusa931209-cmd/Voragon/pull/17) | [dev-step-p5-003-model-cache-pvc.md](dev-step-p5-003-model-cache-pvc.md) |
| P5-004 | Health probes and rolling restart | done | [#17](https://github.com/kazusa931209-cmd/Voragon/pull/17) | [dev-step-p5-004-probes-rolling-restart.md](dev-step-p5-004-probes-rolling-restart.md) |
| P5-005 | K8s dev docs and Phase 5 exit | done | [#17](https://github.com/kazusa931209-cmd/Voragon/pull/17) | [dev-step-p5-005-k8s-dev-docs-exit.md](dev-step-p5-005-k8s-dev-docs-exit.md) |

**Suggested order:** P5-001 → P5-002 → P5-003 → P5-004 → P5-005.

**Phase 5 exit:** signed off 2026-10-15 — [dev-step-phase5-exit.md](dev-step-phase5-exit.md). Dev-steps [P5-001](dev-step-p5-001-kind-cluster.md)–[P5-005](dev-step-p5-005-k8s-dev-docs-exit.md) done.

---

## Phase 6: AWS EKS

| ID | Title | Status | PR | Doc |
|----|-------|--------|-----|-----|
| P6-001 | ECR repository and image push | done | [`4f27196`](https://github.com/kazusa931209-cmd/Voragon/commit/4f27196) | [dev-step-p6-001-ecr-image-push.md](dev-step-p6-001-ecr-image-push.md) |
| P6-002 | EKS cluster and CPU node group | done | — | [dev-step-p6-002-eks-cluster-cpu.md](dev-step-p6-002-eks-cluster-cpu.md) |
| P6-003 | EKS realtime manifests and deploy | done | [`658bdf8`](https://github.com/kazusa931209-cmd/Voragon/commit/658bdf8) | [dev-step-p6-003-eks-realtime-manifests.md](dev-step-p6-003-eks-realtime-manifests.md) |
| P6-004 | ALB Ingress for WebSocket | done | [`487ef89`](https://github.com/kazusa931209-cmd/Voragon/commit/487ef89) | [dev-step-p6-004-alb-ingress-websocket.md](dev-step-p6-004-alb-ingress-websocket.md) |
| P6-005 | API Gateway WebSocket and authentication | done | [`921e438`](https://github.com/kazusa931209-cmd/Voragon/commit/921e438) | [dev-step-p6-005-api-gateway-auth.md](dev-step-p6-005-api-gateway-auth.md) |
| P6-006 | CloudWatch logging | done | [`e5ffb20`](https://github.com/kazusa931209-cmd/Voragon/commit/e5ffb20) | [dev-step-p6-006-cloudwatch-logging.md](dev-step-p6-006-cloudwatch-logging.md) |
| P6-007 | DNS and TLS (Route 53 + ACM) | done | — | [dev-step-p6-007-dns-tls.md](dev-step-p6-007-dns-tls.md) |
| P6-008 | AWS dev docs and Phase 6 exit prep | done | — | [dev-step-p6-008-aws-dev-docs-exit.md](dev-step-p6-008-aws-dev-docs-exit.md) |

**Suggested order:** P6-001 → P6-002 → P6-003 → P6-004 → P6-005 → P6-006 → P6-007 → P6-008 (P6-006 may parallelize after P6-003; P6-007 may overlap P6-004/P6-005 — finish before exit sign-off).

**Phase 6 exit:** signed off **2026-10-16** — [dev-step-phase6-exit.md](dev-step-phase6-exit.md). Dev-steps [P6-001](dev-step-p6-001-ecr-image-push.md)–[P6-008](dev-step-p6-008-aws-dev-docs-exit.md) done.

---

## Phase 7: GPU Inference

| ID | Title | Status | PR | Doc |
|----|-------|--------|-----|-----|
| P7-001 | EKS GPU node pool | done | — | [dev-step-p7-001-gpu-node-pool.md](dev-step-p7-001-gpu-node-pool.md) |
| P7-002 | NVIDIA device plugin | done | — | [dev-step-p7-002-nvidia-device-plugin.md](dev-step-p7-002-nvidia-device-plugin.md) |
| P7-003 | ASR inference image and ECR | done | — | [dev-step-p7-003-asr-image-ecr.md](dev-step-p7-003-asr-image-ecr.md) |
| P7-004 | asr-service Deployment on GPU | done | — | [dev-step-p7-004-asr-service-deploy.md](dev-step-p7-004-asr-service-deploy.md) |
| P7-005 | Model weights on GPU pods | done | — | [dev-step-p7-005-model-weights-gpu.md](dev-step-p7-005-model-weights-gpu.md) |
| P7-006 | Realtime backend remote ASR | done | — | [dev-step-p7-006-realtime-remote-asr.md](dev-step-p7-006-realtime-remote-asr.md) |
| P7-007 | GPU utilization metrics | done | — | [dev-step-p7-007-gpu-metrics.md](dev-step-p7-007-gpu-metrics.md) |
| P7-008 | GPU dev docs and Phase 7 exit prep | done | — | [dev-step-p7-008-gpu-dev-docs-exit.md](dev-step-p7-008-gpu-dev-docs-exit.md) |

**Suggested order:** P7-001 → P7-002 → P7-003 → P7-004 → P7-005 → P7-006 → P7-007 → P7-008 (P7-003 may start in parallel after P7-001; P7-006 requires P7-004 Service reachable).

**Phase 7 exit:** [dev-step-phase7-exit.md](dev-step-phase7-exit.md) — operator E2E sign-off after [phase7-gpu-path.md](../operations/phase7-gpu-path.md). All P7 dev-steps done. See [phases.md](phases.md).

---

## Phase 8: AI Gateway

| ID | Title | Status | PR | Doc |
|----|-------|--------|-----|-----|
| P8-001 | AI Gateway service scaffold | done | — | [dev-step-p8-001-ai-gateway-scaffold.md](dev-step-p8-001-ai-gateway-scaffold.md) |
| P8-002 | AI Gateway model registry | done | — | [dev-step-p8-002-model-registry.md](dev-step-p8-002-model-registry.md) |
| P8-003 | AI Gateway ASR inference proxy | done | [`bd4d9d2`](https://github.com/kazusa931209-cmd/Voragon/commit/bd4d9d2) | [dev-step-p8-003-asr-inference-proxy.md](dev-step-p8-003-asr-inference-proxy.md) |
| P8-004 | AI Gateway backend health checks | done | [`0c84221`](https://github.com/kazusa931209-cmd/Voragon/commit/0c84221) | [dev-step-p8-004-backend-health-checks.md](dev-step-p8-004-backend-health-checks.md) |
| P8-005 | AI Gateway fallback routing | done | [`23e2278`](https://github.com/kazusa931209-cmd/Voragon/commit/23e2278) | [dev-step-p8-005-fallback-routing.md](dev-step-p8-005-fallback-routing.md) |
| P8-006 | Realtime routes via AI Gateway | done | [`da2e19e5`](https://github.com/kazusa931209-cmd/Voragon/commit/da2e19e5) | [dev-step-p8-006-realtime-routes-via-gateway.md](dev-step-p8-006-realtime-routes-via-gateway.md) |
| P8-007 | AI Gateway container image | done | [`6559a795`](https://github.com/kazusa931209-cmd/Voragon/commit/6559a795) | [dev-step-p8-007-ai-gateway-image.md](dev-step-p8-007-ai-gateway-image.md) |
| P8-008 | EKS AI Gateway manifests | in-progress | — | [dev-step-p8-008-eks-ai-gateway-manifests.md](dev-step-p8-008-eks-ai-gateway-manifests.md) |

**Suggested order (planned):** P8-001 → P8-002 (model registry) → P8-003 (ASR inference proxy) → P8-004 (backend health checks) → P8-005 (fallback) → P8-006 (realtime routes via gateway) → P8-007 (container image) → P8-008 (Kind/EKS manifests) → P8-009 (gateway metrics) → P8-010 (ops docs + Phase 8 exit).

**Phase 8 exit:** See [phases.md](phases.md) — realtime-service calls AI Gateway, not ASR directly; model changes via config.

---

## Phase 9+

Dev-steps for Phase 9 and beyond — see [phases.md](phases.md).
