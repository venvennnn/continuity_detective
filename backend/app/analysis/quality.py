import cv2
import numpy as np


def assess(image, pose: dict, polygon: list | None, config: dict) -> tuple:
    metrics = {'visibility': pose.get('visibility', 0), 'presence': pose.get('presence', 0)}
    reasons = []
    if pose.get('reason'):
        reasons.append(pose['reason'])
    if polygon is None:
        return list(dict.fromkeys(reasons + ['unreliable_correspondence'])), metrics, None
    points = np.array(polygon, np.float32)
    if not np.isfinite(points).all() or np.any(points < 0) or np.any(points > 1):
        reasons.append('torso_not_visible')
        return list(dict.fromkeys(reasons)), metrics, None
    if min(metrics['visibility'], metrics['presence']) < config['min_visibility']:
        reasons.append('torso_not_visible')
    height, width = image.shape[:2]
    pixels = np.round(points * [width - 1, height - 1]).astype(np.int32)
    if not cv2.isContourConvex(pixels) or cv2.contourArea(pixels) < 16:
        return list(dict.fromkeys(reasons + ['unreliable_correspondence'])), metrics, None
    x, y, w, h = cv2.boundingRect(pixels)
    metrics['crop_width'], metrics['crop_height'] = w, h
    if min(w, h) < config['min_crop_side']:
        reasons.append('too_small')
    mask = np.zeros((height, width), np.uint8)
    cv2.fillConvexPoly(mask, pixels, 255)
    person = pose.get('person_mask')
    if person is not None:
        person = cv2.resize(person, (width, height))
        covered = float(np.mean(person[mask > 0] > 0.7))
        metrics['person_coverage'] = covered
        if covered < 0.8:
            reasons.append('unreliable_correspondence')
        mask[person < 0.7] = 0
    if np.count_nonzero(mask) < config['min_crop_side'] ** 2:
        return list(dict.fromkeys(reasons + ['too_small'])), metrics, None
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Measure sharpness on a consistent crop resolution to reduce scale effects.
    normalized = cv2.resize(gray[y:y+h, x:x+w], (160, 160))
    laplacian = cv2.Laplacian(normalized, cv2.CV_64F)
    metrics['sharpness'] = float(laplacian.var())
    valid = cv2.resize(mask[y:y+h, x:x+w], (160, 160), interpolation=cv2.INTER_NEAREST)
    valid = cv2.erode(valid, np.ones((5, 5), np.uint8))
    strengths = np.abs(laplacian[valid > 0])
    count = max(1, int(len(strengths) * 0.01))
    metrics['edge_sharpness'] = (float(np.partition(strengths, -count)[-count:].mean())
                                 if len(strengths) else 0.0)
    # Smooth fabric need not have high average texture. Retain a focus check
    # on its strongest valid edges instead of lowering the difference threshold.
    if (metrics['sharpness'] < config['min_sharpness'] and
            metrics['edge_sharpness'] < config['min_edge_sharpness']):
        reasons.append('blurred')
    values = gray[mask > 0]
    metrics['exposure_clipping'] = float(np.mean((values < 8) | (values > 247)))
    if metrics['exposure_clipping'] > config['max_clipping']:
        reasons.append('exposure_extreme')
    return list(dict.fromkeys(reasons)), metrics, mask
