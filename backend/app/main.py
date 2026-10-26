import hashlib
import json
import math
import mimetypes
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse

from . import queue, storage
from .config import ROOT, MODEL, ALGORITHM, DEFAULT_CONFIG
from .schemas import AnalysisRequest, FrameRequest, SequenceRequest

app = FastAPI(title='Continuity Detective local API')


def fail(code, message, status=422):
    raise HTTPException(status_code=status, detail={'code': code, 'message': message})


@app.exception_handler(HTTPException)
async def http_error(request, error):
    detail = error.detail if isinstance(error.detail, dict) else {'code': 'http_error', 'message': str(error.detail)}
    return JSONResponse(status_code=error.status_code, content=detail)


@app.exception_handler(RequestValidationError)
async def validation_error(request, error):
    return JSONResponse(status_code=422, content={'code': 'invalid_input', 'message': 'Check the supplied input fields.'})


@app.exception_handler(FileNotFoundError)
async def missing_file(request, error):
    return JSONResponse(status_code=404, content={'code': 'media_unavailable', 'message': 'Local media or evidence is unavailable. Relink the original file.'})


@app.exception_handler(ValueError)
async def invalid_value(request, error):
    return JSONResponse(status_code=422, content={'code': 'invalid_input', 'message': str(error)})


@app.middleware('http')
async def local_browser_origin(request, call_next):
    origin = request.headers.get('origin')
    if origin and origin not in {'http://127.0.0.1:5173', 'http://localhost:5173',
                                 'http://127.0.0.1:5174', 'http://localhost:5174',
                                 'http://127.0.0.1:8000', 'http://localhost:8000'}:
        return JSONResponse(status_code=403, content={'code': 'origin_denied', 'message': 'Use the local workbench.'})
    return await call_next(request)


def get_clip(identity, prepared=False):
    storage.safe_id(identity)
    clip = storage.get_clip(identity, prepared=prepared)
    if not Path(clip['media_path']).is_file():
        fail('media_unavailable', 'Original clip is missing; relink it before playback or analysis.', 404)
    return clip


def get_clips(identities, prepared=True):
    clips = [get_clip(identity, prepared=prepared) for identity in identities]
    if sum(clip['size'] for clip in clips) > 250 * 1024 * 1024:
        fail('sequence_too_large', 'The current sequence limit is 250 MiB.', 413)
    return clips


@app.get('/api/health')
def health():
    return {'api': 'ok', 'worker': queue.worker_status(), 'ffmpeg': bool(shutil.which('ffmpeg')),
            'ffprobe': bool(shutil.which('ffprobe')), 'model_available': MODEL.is_file(),
            'algorithm': ALGORITHM, 'calibration_status': 'provisional'}


@app.get('/api/demo')
def demo():
    from .analysis.media import digest_file
    from .analysis.references import canonical_hash
    from .analysis.pipeline import register_clip
    clips, jobs = [], []
    model_hash = digest_file(MODEL) if MODEL.is_file() else None
    for index in range(3):
        source = ROOT / f'take{index+1}.mp4'
        if not source.is_file():
            continue
        identity = f'clip-{index}'
        source_hash = digest_file(source)
        try:
            prepared = storage.get_clip(identity, prepared=True)
            first = prepared['samples'][0]
            expected = canonical_hash({'source': source_hash, 'clip_id': identity, 'pts': first['pts'],
                                       'model': model_hash, 'algorithm': ALGORITHM})
            if prepared['source_hash'] != source_hash or first['id'] != expected:
                raise ValueError('Cached preparation is obsolete')
            clips.append(storage.public_clip(prepared))
        except (FileNotFoundError, ValueError, KeyError, IndexError):
            clip = register_clip(source, identity)
            clips.append(storage.public_clip(clip))
            jobs.append({'clip_id': identity, 'job_id': queue.enqueue('prepare', {'clip_id': identity})})
    return {'clips': clips, 'jobs': jobs}


async def receive_file(file: UploadFile):
    folder = storage.DATA / 'uploads'
    folder.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or 'clip.mp4').suffix.lower()
    if suffix not in {'.mp4', '.mov', '.webm', '.mkv'}:
        fail('unsupported_media', 'Choose an MP4, MOV, WebM or MKV video.')
    path = folder / (uuid.uuid4().hex + suffix)
    total = 0
    try:
        with path.open('wb') as target:
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > 250 * 1024 * 1024:
                    fail('clip_too_large', 'The current upload limit is 250 MiB.', 413)
                target.write(chunk)
        if total == 0:
            fail('empty_media', 'The selected file is empty.')
        return path
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()


@app.post('/api/clips')
async def upload_clip(file: UploadFile = File(...), project_id: str = Form('local')):
    from .analysis.pipeline import register_clip
    storage.safe_id(project_id)
    original_name = Path(file.filename or 'clip.mp4').name
    path = await receive_file(file)
    try:
        clip = register_clip(path, uuid.uuid4().hex)
        clip['filename'] = original_name
        storage.write_json(storage.clip_path(clip['id']), clip)
    finally:
        path.unlink(missing_ok=True)
    identity = queue.enqueue('prepare', {'clip_id': clip['id']})
    return {'clip': storage.public_clip(clip), 'job_id': identity}


@app.get('/api/clips/{identity}')
def clip_status(identity: str):
    try:
        clip = storage.get_clip(identity, prepared=True)
    except FileNotFoundError:
        clip = storage.get_clip(identity)
    return storage.public_clip(clip)


@app.get('/api/media/{identity}')
def media(identity: str):
    clip = get_clip(identity)
    path = Path(clip['media_path'])
    return FileResponse(path, media_type=mimetypes.guess_type(path.name)[0] or 'video/mp4',
                        headers={'Accept-Ranges': 'bytes'})


@app.get('/api/assets/{identity}')
def asset(identity: str):
    path = storage.evidence_path(identity)
    if not path.is_file():
        raise FileNotFoundError(path)
    return FileResponse(path, media_type='image/jpeg', headers={'Cache-Control': 'private, max-age=31536000, immutable'})


@app.post('/api/frames')
def frame(request: FrameRequest):
    clip = get_clip(request.clip_id, prepared=True)
    if request.time_ms > clip['metadata']['duration_ms']:
        fail('invalid_position', 'The selected time is outside the clip.')
    return {'job_id': queue.enqueue('extract_frame', request.model_dump())}


@app.get('/api/jobs/{identity}')
def job(identity: str):
    result = queue.get(identity)
    if result is None:
        fail('job_not_found', 'Job not found.', 404)
    return {key: result[key] for key in ['id', 'state', 'phase', 'completed', 'total', 'error', 'result', 'updated']}


@app.post('/api/analysis-runs')
def analysis(request: AnalysisRequest):
    from .analysis.references import canonical_hash
    clips = get_clips(request.clip_ids)
    references = [reference.model_dump() for reference in request.references]
    positions = []
    for reference in references:
        if reference['start_clip_id'] not in request.clip_ids:
            fail('invalid_reference', 'Reference boundary must belong to the sequence.')
        index = request.clip_ids.index(reference['start_clip_id'])
        if reference['start_ms'] > clips[index]['metadata']['duration_ms']:
            fail('invalid_reference', 'Reference boundary is outside its clip.')
        evidence = storage.read_json(storage.evidence_path(reference['evidence_id'], 'evidence.json'))
        if evidence['clip_id'] not in request.clip_ids:
            fail('invalid_reference', 'Reference evidence must belong to the sequence.')
        positions.append((index, reference['start_ms']))
    if positions[0] != (0, 0) or any(b <= a for a, b in zip(positions, positions[1:])):
        fail('invalid_reference_order', 'References must cover sequence start and have increasing boundaries.')
    config = request.config or {}
    if any(key not in DEFAULT_CONFIG or key == 'calibration_status' for key in config):
        fail('invalid_config', 'Unknown analysis configuration.')
    limits = {'sample_interval_ms': (100, 5000), 'difference_threshold': (0, 1),
              'min_visibility': (0, 1), 'min_crop_side': (8, 500), 'min_sharpness': (0, 10000),
              'min_edge_sharpness': (0, 10000), 'max_clipping': (0, 1), 'histogram_bins': (4, 64)}
    for key, value in config.items():
        if not isinstance(value, (int, float)) or not math.isfinite(value) or not limits[key][0] <= value <= limits[key][1]:
            fail('invalid_config', 'Analysis configuration is outside supported limits.')
        if key in {'histogram_bins', 'min_crop_side', 'sample_interval_ms'} and (isinstance(value, bool) or int(value) != value):
            fail('invalid_config', 'This analysis configuration field requires an integer.')
    payload = request.model_dump()
    payload['references'] = references
    payload['source_hashes'] = {clip['id']: clip['source_hash'] for clip in clips}
    payload['run_id'] = uuid.uuid4().hex
    payload['input_fingerprint'] = canonical_hash({**request.model_dump(), 'source_hashes': payload['source_hashes']})
    identity = queue.enqueue('analyse', payload)
    return {'run_id': payload['run_id'], 'job_id': identity, 'input_fingerprint': payload['input_fingerprint']}


@app.post('/api/sequences')
def sequence(request: SequenceRequest):
    from .sequence import sequence_id
    clips = get_clips(request.clip_ids)
    identity = sequence_id(clips)
    manifest = storage.DATA / 'sequences' / identity / 'manifest.json'
    video = manifest.parent / 'video.mp4'
    cached = storage.read_json(manifest) if manifest.is_file() and video.is_file() else None
    return {'sequence_id': identity, 'job_id': queue.enqueue('sequence', request.model_dump(), result=cached)}


@app.get('/api/sequences/{identity}/video')
def sequence_video(identity: str):
    storage.safe_id(identity)
    path = storage.DATA / 'sequences' / identity / 'video.mp4'
    if not path.is_file():
        raise FileNotFoundError(path)
    return FileResponse(path, media_type='video/mp4', headers={'Accept-Ranges': 'bytes'})


@app.post('/api/clips/{identity}/relink')
async def relink(identity: str, file: UploadFile = File(...)):
    from .analysis.media import digest_file
    clip = storage.get_clip(identity)
    path = await receive_file(file)
    try:
        if digest_file(path) != clip['source_hash']:
            fail('source_mismatch', 'This file does not match the original source content.', 409)
        target = Path(clip['media_path'])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    finally:
        path.unlink(missing_ok=True)
    return {'id': identity, 'available': True}
