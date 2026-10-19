# Voragon Docker (local backend)

Run the **realtime backend** in Docker; keep the **desktop app on the host** for microphone capture.

## Quick start

```bash
# Terminal 1 — backend (from repo root)
cd docker
docker compose up --build
```

Compose project name: **`voragon`**. Wait until healthy (first run may take several minutes while models download into the `voragon-model-cache` volume):

```bash
curl -f http://localhost:8000/health
```

```bash
# Terminal 2 — desktop (from repo root)
cd desktop
pnpm install
pnpm tauri dev
```

In the app: **Connect** (default `ws://localhost:8000/v1/realtime`) → **Start transcription** → speak.

## When to use Docker vs bare-metal backend

| Use Docker | Use bare-metal (`backend/` venv) |
|------------|----------------------------------|
| Reproducible CPU stack without local Python/ASR deps | Backend hacking, pytest, debugger |
| Matches Phase 4 compose path | Faster iteration on backend code |
| Model cache via named volume ([P4-003](../docs/roadmap/dev-step-p4-003-model-cache-volumes.md)) | `ASR_BACKEND=mock` for quick tests |

## Useful commands

```bash
cd docker
docker compose ps
docker compose down          # keeps model cache volume
docker compose down -v       # wipe model cache
docker compose -p docker down   # remove old stack if you used the folder name before `name: voragon`
```

## More detail

- [Docker Compose ops doc](../docs/operations/docker.md)
- [Local development](../docs/operations/local-development.md)
- [Realtime backend image](realtime-backend/README.md)
- [AI Gateway image](ai-gateway/README.md) (Phase 8)
