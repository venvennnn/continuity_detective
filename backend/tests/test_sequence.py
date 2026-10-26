import shutil
import subprocess

import pytest

from backend.app import storage
from backend.app.analysis.media import probe
from backend.app.sequence import build_sequence


@pytest.mark.skipif(not shutil.which('ffmpeg'), reason='FFmpeg required')
def test_merged_playback_preserves_source_order_and_offsets(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, 'DATA', tmp_path)
    clips = []
    for identity, dimensions in [('a', '640x360'), ('b', '320x480')]:
        source = tmp_path / f'{identity}.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                        f'testsrc2=size={dimensions}:rate=24:duration=0.5',
                        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(source)], check=True, timeout=30)
        clips.append({'id': identity, 'source_hash': identity, 'media_path': str(source), 'metadata': probe(source)})
    result = build_sequence(clips)
    assert result['duration_ms'] == pytest.approx(1000)
    assert result['segments'][1]['offset_ms'] == pytest.approx(500)
    merged = storage.DATA / 'sequences' / result['id'] / 'video.mp4'
    metadata = probe(merged)
    assert metadata['width'] == 1280
    assert metadata['height'] == 720
    assert metadata['duration_ms'] == pytest.approx(1000, abs=50)
    assert build_sequence(clips) == result
