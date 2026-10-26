import shutil
import subprocess

import pytest

from backend.app.analysis.media import probe, extract_frame, sample_frames


@pytest.mark.skipif(not shutil.which('ffmpeg'), reason='FFmpeg not installed')
def test_source_pts_and_exact_decode(tmp_path):
    path = tmp_path / 'timing.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                    'testsrc2=size=160x240:rate=7:duration=1', '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p', str(path)], check=True, timeout=30)
    metadata = probe(path)
    assert len(metadata['frames']) == 7
    assert metadata['frames'][1]['time_ms'] == pytest.approx(1000 / 7)
    assert metadata['frames'][1]['pts'] > 0
    assert extract_frame(path, 1).shape[:2] == (240, 160)
    assert sample_frames(metadata)[-1]['ordinal'] == 6


@pytest.mark.skipif(not shutil.which('ffmpeg'), reason='FFmpeg not installed')
def test_variable_frame_rate_preserves_presentation_time(tmp_path):
    path = tmp_path / 'vfr.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                    'testsrc2=size=160x240:rate=10:duration=1', '-vf',
                    'select=not(eq(n\\,1)+eq(n\\,4)+eq(n\\,5))',
                    '-fps_mode', 'vfr', '-c:v', 'libx264', str(path)], check=True, timeout=30)
    metadata = probe(path)
    times = [frame['time_ms'] for frame in metadata['frames']]
    assert times[:4] == pytest.approx([0, 200, 300, 600])
    assert metadata['frames'][3]['ordinal'] == 3
    assert extract_frame(path, 3).shape[:2] == (240, 160)


@pytest.mark.skipif(not shutil.which('ffmpeg'), reason='FFmpeg not installed')
def test_rotation_metadata_matches_displayed_evidence(tmp_path):
    source = tmp_path / 'source.mp4'
    rotated = tmp_path / 'rotated.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                    'testsrc2=size=160x240:rate=2:duration=1', '-c:v', 'libx264',
                    str(source)], check=True, timeout=30)
    subprocess.run(['ffmpeg', '-v', 'error', '-display_rotation', '90', '-i', str(source),
                    '-c', 'copy', str(rotated)], check=True, timeout=30)
    assert abs(probe(rotated)['rotation']) == 90
    assert extract_frame(rotated, 0).shape[:2] == (160, 240)
