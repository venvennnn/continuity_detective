# Continuity Detective

Local video wardrobe inspection for short-form creators. Implementation is in progress; see `devpost/checklist.md` for verified progress and `validation/report.md` for capability status.

## Evidence inspector

Requires Python 3.11 and FFmpeg/ffprobe on PATH. From the repository root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m backend.scripts.fetch_model
.\.venv\Scripts\python.exe -m backend.scripts.inspect_sequence path/to/clip1.mp4 path/to/clip2.mp4 --reference 0:0 --new-reference 1:1000
```

Reference arguments are zero-based clip index and source-relative milliseconds. The inspector decodes the nearest actual source frame and records its resolved time. The command explicitly confirms these reference selections. Use `--crop X Y W H` to override the initial crop with normalized image coordinates. The output JSON and its `.html` evidence companion are written under ignored `data/`; open the HTML locally to inspect A/B frames and measured crop overlays. Outputs are experimental measured differences, not confidence estimates. Use one to three clips, each at most 30 seconds.

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest backend/tests -q
```

The browser workbench, API and separate worker are implemented. Start them using the commands below. No paid APIs, accounts, cloud sync or automatic repair are involved. Do not commit local footage, downloaded models, environment files or personal learner context.

Model: Google MediaPipe Pose Landmarker Lite float16 version 1, downloaded explicitly from the official MediaPipe model bucket. Model URL and verified SHA-256 are recorded in `backend/scripts/fetch_model.py`; follow the upstream model license/provenance before redistribution. Model files are excluded from Git.

## Run the workbench

Install frontend dependencies once with `npm --prefix frontend install`. From the repository root, run each command in a separate terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

```powershell
.\.venv\Scripts\python.exe -m backend.app.worker
```

```powershell
npm --prefix frontend run dev -- --host 127.0.0.1 --port 5174 --strictPort
```

Open http://127.0.0.1:5174. Port 5174 avoids the earlier ContagionCut development server on 5173. The supplied root-level take1.mp4, take2.mp4 and take3.mp4 are local-only demo inputs. On first opening, preparation and actual sequence concatenation run without comparing wardrobes. Click **Review reference**, adjust the crop if needed, and **Use this reference** to run comparison. Findings seek the continuous video at the appropriate combined timestamp. The supplied clips cut at 00:08 and 00:16.

- **Sequence playback:** actual 24-second concatenation, computed in-video sample annotations, timeline markers, optional pause at flagged shots.
- **Evidence A/B:** exact analysed frames/crops and source playback at the original timestamps.
- **New wardrobe from here:** confirmation creates a forward reference segment and recomputes results. Earlier reference segments remain intact.
- **Review:** Needs fix, Intentional, False positive, Defer; separately mark a region not assessable due to occlusion/blur/ambiguity. Human assessment never rewrites automatic measurements.
- **Resume/export:** browser IndexedDB restores the last project and cached evidence without automatic analysis. JSON export embeds evidence images and reference/review history.

Appearance difference is a measured colour distance, not confidence or proof of garment identity. Sampling can miss brief events. Foreground occlusion is not reliably detected automatically; human assessment remains necessary. Prop/face/repair/regeneration capabilities are absent.

## Verify the running workflow

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
npm --prefix frontend run build
npm --prefix frontend exec -- playwright install chromium
npm --prefix frontend run test:e2e
```

The browser test expects the three local processes running and the supplied real takes available; these clips are deliberately excluded from the public repository. See validation/report.md for the scope of measured validation. A future reviewer must supply their own appropriately licensed clips or obtain permission to use the demo sources.
