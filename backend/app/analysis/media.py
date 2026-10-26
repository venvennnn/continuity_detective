"""Decoded ordinals and source PTS, never estimated frame numbers."""
import hashlib
import json
import subprocess
from fractions import Fraction
from pathlib import Path

import cv2
import numpy as np


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def probe(path: Path) -> dict:
    args = ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_streams', '-show_frames', '-show_entries',
            'stream=width,height,time_base,duration:stream_tags=rotate:stream_side_data=rotation:'
            'frame=best_effort_timestamp,best_effort_timestamp_time', '-of', 'json', str(path)]
    output = subprocess.run(args, capture_output=True, check=True, timeout=120)
    info = json.loads(output.stdout)
    if not info.get('streams'):
        raise ValueError('No video stream found')
    stream = info['streams'][0]
    rotation = int(stream.get('tags', {}).get('rotate', 0))
    for side in stream.get('side_data_list', []):
        rotation = int(side.get('rotation', rotation))
    frames = []
    for ordinal, frame in enumerate(info.get('frames', [])):
        if 'best_effort_timestamp' not in frame:
            raise ValueError('Source frame is missing a reliable presentation timestamp')
        pts = int(frame['best_effort_timestamp'])
        frames.append({'ordinal': ordinal, 'pts': pts,
                       'source_ms': float(Fraction(pts) * Fraction(stream['time_base']) * 1000)})
    if not frames:
        raise ValueError('No decodable timestamped video frames')
    origin = frames[0]['source_ms']
    for frame in frames:
        frame['time_ms'] = frame['source_ms'] - origin
    duration_ms = max(float(stream.get('duration', 0) or 0) * 1000,
                      frames[-1]['time_ms'])
    return {'width': stream['width'], 'height': stream['height'],
            'rotation': rotation, 'time_base': stream['time_base'],
            'duration_ms': duration_ms, 'frames': frames}


def sample_frames(metadata: dict, interval_ms: int = 500) -> list[dict]:
    frames = metadata['frames']
    selected = {0, len(frames) - 1}
    next_ms = interval_ms
    for i, frame in enumerate(frames):
        if frame['time_ms'] >= next_ms:
            selected.add(i)
            next_ms = frame['time_ms'] + interval_ms
    return [frames[i] for i in sorted(selected)]


def extract_frame(path: Path, ordinal: int) -> np.ndarray:
    # Decode by ordinal; accurate for VFR and non-keyframes. FFmpeg autorotates.
    args = ['ffmpeg', '-v', 'error', '-i', str(path), '-vf',
            f"select=eq(n\\,{ordinal}),scale=w='min(960,iw)':h='min(960,ih)':force_original_aspect_ratio=decrease",
            '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', 'pipe:1']
    output = subprocess.run(args, capture_output=True, check=True, timeout=120)
    image = cv2.imdecode(np.frombuffer(output.stdout, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f'Could not decode frame {ordinal}')
    return image


def write_image(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), image):
        raise OSError(f'Cannot save evidence image {path.name}')
