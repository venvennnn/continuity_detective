"""Local media identities and public, path-free response documents."""
import json
import re
from pathlib import Path

from backend.app.config import DATA as DEFAULT_DATA

DATA = DEFAULT_DATA
ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]{1,80}$')


def safe_id(value: str) -> str:
    if not ID_PATTERN.fullmatch(value):
        raise ValueError('Invalid local object identifier')
    return value


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, allow_nan=False), encoding='utf-8')
    temporary.replace(path)


def clip_path(clip_id: str) -> Path:
    return DATA / 'clips' / f'{safe_id(clip_id)}.json'


def get_clip(clip_id: str, prepared=False):
    folder = 'prepared' if prepared else 'clips'
    return read_json(DATA / folder / f'{safe_id(clip_id)}.json')


def public_clip(clip: dict):
    result = {key: value for key, value in clip.items() if key != 'media_path'}
    result['media_url'] = f"/api/media/{clip['id']}"
    result['available'] = Path(clip['media_path']).is_file()
    return result


def evidence_path(identity: str, filename='frame.jpg') -> Path:
    if not re.fullmatch(r'[a-f0-9]{64}', identity):
        raise ValueError('Invalid evidence identifier')
    return DATA / 'evidence' / identity / filename

