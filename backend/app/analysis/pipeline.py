import hashlib
import json
import shutil
from pathlib import Path

import cv2
import numpy as np

from backend.app.config import DATA, MODEL, DEFAULT_CONFIG, ALGORITHM
from .media import probe, digest_file, sample_frames, extract_frame, write_image
from .pose import TorsoDetector, box_from_polygon, map_crop
from .quality import assess
from .wardrobe import histogram, distance
from .references import canonical_hash, resolve_reference


def save_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')
    temporary.replace(path)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def register_clip(path: Path, clip_id: str | None = None):
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError('Select a nonempty local video file')
    source_hash = digest_file(path)
    destination = DATA / 'media' / source_hash / ('source' + path.suffix.lower())
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        shutil.copyfile(path, destination)
    clip = {'id': clip_id or source_hash[:16], 'source_hash': source_hash,
            'filename': path.name, 'media_path': str(destination), 'size': path.stat().st_size}
    save_json(DATA / 'clips' / f"{clip['id']}.json", clip)
    return clip


def frame_evidence(clip, metadata, frame, detector, config):
    image = extract_frame(Path(clip['media_path']), frame['ordinal'])
    pose = detector.detect(image)
    model_hash = digest_file(MODEL)
    identity = canonical_hash({'source': clip['source_hash'], 'clip_id': clip['id'], 'pts': frame['pts'],
                               'model': model_hash, 'algorithm': ALGORITHM})
    folder = DATA / 'evidence' / identity
    folder.mkdir(parents=True, exist_ok=True)
    write_image(folder / 'frame.jpg', image)
    person_mask = pose.pop('person_mask', None)
    if person_mask is not None:
        write_image(folder / 'person-mask.png', (person_mask * 255).astype(np.uint8))
    polygon = pose.get('polygon')
    crop = box_from_polygon(polygon) if polygon else [0.2, 0.2, 0.6, 0.6]
    x, y, w, h = crop
    proposed_polygon = [[x, y], [x+w, y], [x+w, y+h], [x, y+h]] if polygon else None
    quality_pose = {**pose, 'person_mask': person_mask}
    reasons, metrics, _ = assess(image, quality_pose, proposed_polygon, config)
    evidence = {'id': identity, 'clip_id': clip['id'], 'source_hash': clip['source_hash'],
                **frame, 'time_base': metadata['time_base'], 'rotation': metadata['rotation'],
                'width': image.shape[1], 'height': image.shape[0],
                'image_hash': digest_file(folder / 'frame.jpg'),
                'asset_id': identity, 'pose': pose,
                'crop': crop,
                'crop_origin': 'pose' if polygon else 'manual_selection_aid',
                'quality_reasons': reasons, 'quality': metrics,
                'model_hash': model_hash}
    save_json(folder / 'evidence.json', evidence)
    return evidence


def prepare_clip(clip, config=None, progress=lambda *args: None):
    config = {**DEFAULT_CONFIG, **(config or {})}
    metadata = probe(Path(clip['media_path']))
    if metadata['duration_ms'] > 30_100:
        raise ValueError('Clip exceeds the current 30-second limit')
    selected = sample_frames(metadata, config['sample_interval_ms'])
    detector = TorsoDetector(MODEL)
    evidence = []
    try:
        for i, frame in enumerate(selected):
            evidence.append(frame_evidence(clip, metadata, frame, detector, config))
            progress(i + 1, len(selected), 'Preparing frames')
    finally:
        detector.close()
    result = {**clip, 'metadata': metadata, 'samples': evidence,
              'proposal_id': next((e['id'] for e in evidence if not e['quality_reasons']), None)}
    save_json(DATA / 'prepared' / f"{clip['id']}.json", result)
    return result


def extract_selected(clip, time_ms):
    metadata = probe(Path(clip['media_path']))
    frame = min(metadata['frames'], key=lambda f: abs(f['time_ms'] - time_ms))
    detector = TorsoDetector(MODEL)
    try:
        return frame_evidence(clip, metadata, frame, detector, DEFAULT_CONFIG)
    finally:
        detector.close()


def load_evidence(identity):
    return read_json(DATA / 'evidence' / identity / 'evidence.json')


def evidence_pixels(evidence):
    folder = DATA / 'evidence' / evidence['id']
    image = cv2.imread(str(folder / 'frame.jpg'))
    if image is None:
        raise FileNotFoundError('Evidence image unavailable')
    mask = cv2.imread(str(folder / 'person-mask.png'), cv2.IMREAD_GRAYSCALE)
    pose = {**evidence['pose'], 'person_mask': mask.astype(np.float32) / 255 if mask is not None else None}
    return image, pose


def compare(reference, candidate, config):
    ref_evidence = load_evidence(reference['evidence_id'])
    ref_image, ref_pose = evidence_pixels(ref_evidence)
    image, pose = evidence_pixels(candidate)
    x, y, w, h = reference['crop']
    ref_polygon = [[x, y], [x+w, y], [x+w, y+h], [x, y+h]]
    candidate_polygon = None
    if ref_pose.get('polygon') and pose.get('polygon'):
        candidate_polygon = map_crop(ref_pose['polygon'], reference['crop'], pose['polygon'])
    ref_reasons, ref_metrics, ref_mask = assess(ref_image, ref_pose, ref_polygon, config)
    reasons, metrics, mask = assess(image, pose, candidate_polygon, config)
    reasons = [f'reference_{r}' for r in ref_reasons] + reasons
    score = None
    if not reasons:
        score = distance(histogram(ref_image, ref_mask, config['histogram_bins']),
                         histogram(image, mask, config['histogram_bins']))
    status = ('not_assessable' if reasons else
              'difference' if score >= config['difference_threshold'] else 'no_difference_flagged')
    ref_mask_hash = hashlib.sha256(ref_mask.tobytes()).hexdigest() if ref_mask is not None else None
    mask_hash = hashlib.sha256(mask.tobytes()).hexdigest() if mask is not None else None
    fingerprint = canonical_hash({'reference': reference, 'reference_image': ref_evidence['image_hash'],
                                  'candidate': candidate['image_hash'], 'pts': candidate['pts'],
                                  'source': candidate['source_hash'], 'clip_id': candidate['clip_id'],
                                  'candidate_polygon': candidate_polygon,
                                  'reference_mask_hash': ref_mask_hash, 'candidate_mask_hash': mask_hash,
                                  'reference_quality': ref_metrics, 'candidate_quality': metrics,
                                  'assessment_reasons': reasons,
                                  'model': candidate['model_hash'], 'algorithm': ALGORITHM, 'config': config})
    return {'id': fingerprint, 'fingerprint': fingerprint, 'reference_id': reference['id'],
            'reference_evidence': {**ref_evidence, 'crop': reference['crop'], 'effective_polygon': ref_polygon,
                                   'effective_mask_hash': ref_mask_hash},
            'candidate_evidence': {**candidate, 'effective_polygon': candidate_polygon,
                                   'effective_mask_hash': mask_hash},
            'status': status, 'score': None if score is None else score * 100,
            'raw_distance': score, 'threshold': config['difference_threshold'] * 100,
            'reasons': list(dict.fromkeys(reasons)), 'quality': metrics, 'reference_quality': ref_metrics,
            'description': ('Not assessable' if reasons else 'Wardrobe colour difference — review'
                            if status == 'difference' else 'No colour difference flagged'),
            'decision': 'needs_fix' if status == 'difference' else None}


def analyse(clips, references, config=None, progress=lambda *args: None):
    if not references or not all(ref.get('confirmed') for ref in references):
        raise ValueError('Explicitly confirmed wardrobe reference required')
    config = {**DEFAULT_CONFIG, **(config or {})}
    order = [clip['id'] for clip in clips]
    results = []
    samples = [(clip, evidence) for clip in clips for evidence in clip['samples']]
    # Exact selected reference boundaries must be analysed, even between samples.
    known = {(clip['id'], e['pts']) for clip, e in samples}
    for reference in references:
        e = load_evidence(reference['evidence_id'])
        if (e['clip_id'], e['pts']) not in known:
            clip = next(c for c in clips if c['id'] == e['clip_id'])
            samples.append((clip, e))
            known.add((e['clip_id'], e['pts']))
    samples.sort(key=lambda item: (order.index(item[0]['id']), item[1]['time_ms']))
    for i, (clip, evidence) in enumerate(samples):
        reference = resolve_reference(references, clip['id'], evidence['time_ms'], order)
        results.append(compare(reference, evidence, config))
        progress(i + 1, len(samples), 'Comparing wardrobe appearance')
    return {'algorithm': ALGORITHM, 'config': config, 'references': references, 'results': results,
            'coverage': {'sample_interval_ms': config['sample_interval_ms'], 'samples': len(samples),
                         'note': 'Only listed samples assessed; brief intervening events may be missed.'},
            'validation_status': 'experimental_not_independently_validated'}
