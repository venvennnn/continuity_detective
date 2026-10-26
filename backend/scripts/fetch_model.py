"""Explicit, versioned download. Runtime never downloads models."""
import hashlib
import urllib.request

from backend.app.config import MODEL

MODEL_URL = ('https://storage.googleapis.com/mediapipe-models/pose_landmarker/'
             'pose_landmarker_lite/float16/1/pose_landmarker_lite.task')
# SHA-256 verified against the downloaded official version-1 model bundle.
MODEL_SHA256 = '59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a'


def main():
    if not MODEL_SHA256:
        raise RuntimeError('Model checksum must be pinned by setup verification first')
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    content = MODEL.read_bytes() if MODEL.exists() else urllib.request.urlopen(MODEL_URL, timeout=120).read()
    actual = hashlib.sha256(content).hexdigest()
    if actual != MODEL_SHA256:
        raise RuntimeError(f'Model checksum mismatch: {actual}')
    MODEL.write_bytes(content)
    print(f'Verified model {actual}')


if __name__ == '__main__':
    main()
