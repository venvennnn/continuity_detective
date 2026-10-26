# Continuity Detective

Continuity Detective is a local browser workbench for inspecting wardrobe colour continuity across a short sequence of video clips.

## What it does

Load two or three short clips, confirm a torso/wardrobe reference, compare later frames against that reference, review findings with A/B evidence, and export the results as JSON. Footage stays on this computer. There are no cloud accounts or paid APIs.

## Prerequisites

- Node.js and npm
- Python 3.11
- FFmpeg and ffprobe on your PATH

## Installation

From the repository root:

```bash
py -3.11 -m venv .venv
.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
.venv/Scripts/python.exe -m backend.scripts.fetch_model
npm --prefix frontend install
```

On macOS or Linux, use `.venv/bin/python` instead of `.venv/Scripts/python.exe`.

## Running

Start each command from the repository root, in its own terminal:

```bash
.venv/Scripts/python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

```bash
.venv/Scripts/python.exe -m backend.app.worker
```

```bash
npm --prefix frontend run dev -- --host 127.0.0.1 --port 5174 --strictPort
```

Open http://127.0.0.1:5174

The Vite app lives in `frontend/` (there is no root `npm run dev`). It proxies `/api` to port 8000. Put `take1.mp4`, `take2.mp4`, and `take3.mp4` in the repo root and click **Open supplied takes**, or import your own clips (up to three, 30 seconds each, 250 MiB total).

## Build and test

```bash
npm --prefix frontend run build
npm --prefix frontend run test:e2e
.venv/Scripts/python.exe -m pytest backend/tests -q
```

Playwright expects the API, worker, and frontend to be running, plus local demo takes. Those clips are not committed.

## Planning documents

Scope, PRD, and spec live in the `devpost/` folder (`scope.md`, `prd.md`, `spec.md`).

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
