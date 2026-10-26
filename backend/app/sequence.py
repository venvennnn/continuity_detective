"""Browser playback proxy with source segment offsets; source evidence stays unchanged."""
import json
import subprocess
from pathlib import Path

from . import storage
from .analysis.references import canonical_hash


def sequence_id(clips):
    return canonical_hash({'version': 'sequence-1280x720-h264-aac-v1',
                           'clips': [(c['id'], c['source_hash']) for c in clips]})


def build_sequence(clips, progress=lambda *args: None):
    identity = sequence_id(clips)
    folder = storage.DATA / 'sequences' / identity
    manifest = folder / 'manifest.json'
    video = folder / 'video.mp4'
    if manifest.is_file() and video.is_file():
        return storage.read_json(manifest)
    folder.mkdir(parents=True, exist_ok=True)
    inputs, filters, segments = [], [], []
    offset = 0.0
    for index, clip in enumerate(clips):
        metadata = clip['metadata']
        duration = float(metadata['duration_ms']) / 1000
        source = Path(clip['media_path'])
        inputs += ['-i', str(source)]
        audio_info = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a:0',
                                     '-show_entries', 'stream=index', '-of', 'json', str(source)],
                                    capture_output=True, check=True, timeout=30)
        has_audio = bool(json.loads(audio_info.stdout).get('streams'))
        filters.append(f'[{index}:v:0]setpts=PTS-STARTPTS,'
                       'scale=1280:720:force_original_aspect_ratio=decrease,'
                       'pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24,format=yuv420p'
                       f'[v{index}]')
        if has_audio:
            filters.append(f'[{index}:a:0]aresample=48000,aformat=channel_layouts=stereo,'
                           f'apad,atrim=duration={duration},asetpts=PTS-STARTPTS[a{index}]')
        else:
            filters.append(f'anullsrc=r=48000:cl=stereo,atrim=duration={duration},'
                           f'asetpts=PTS-STARTPTS[a{index}]')
        segments.append({'clip_id': clip['id'], 'offset_ms': offset,
                         'duration_ms': metadata['duration_ms']})
        offset += metadata['duration_ms']
    filters.append(''.join(f'[v{i}][a{i}]' for i in range(len(clips))) +
                   f'concat=n={len(clips)}:v=1:a=1[v][a]')
    temporary = folder / 'encoding.mp4'
    progress(0, 1, 'Combining ordered clips')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(filters),
                    '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
                    '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', str(temporary)],
                   capture_output=True, check=True, timeout=300)
    temporary.replace(video)
    result = {'id': identity, 'url': f'/api/sequences/{identity}/video',
              'duration_ms': offset, 'segments': segments,
              'note': 'Playback proxy. Original decoded frames and source PTS remain the evidence authority.'}
    storage.write_json(manifest, result)
    progress(1, 1, 'Sequence ready')
    return result

