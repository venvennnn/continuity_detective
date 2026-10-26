from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class TorsoDetector:
    def __init__(self, model: Path):
        if not model.is_file():
            raise FileNotFoundError('Pose model missing. Run python -m backend.scripts.fetch_model')
        options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(model)),
            running_mode=vision.RunningMode.IMAGE, num_poses=2,
            output_segmentation_masks=True,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5)
        self.detector = vision.PoseLandmarker.create_from_options(options)

    def close(self):
        self.detector.close()

    def detect(self, image: np.ndarray) -> dict:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        result = self.detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
        if len(result.pose_landmarks) != 1:
            return {'reason': 'ambiguous_subject' if result.pose_landmarks else 'torso_not_visible',
                    'polygon': None, 'person_mask': None, 'visibility': 0}
        landmarks = result.pose_landmarks[0]
        # Left shoulder, right shoulder, right hip, left hip, in polygon order.
        shoulders = [landmarks[i] for i in [11, 12]]
        hips = [landmarks[i] for i in [23, 24]]
        # Clothing above the table can be assessable even when hips are offscreen.
        # Infer only the upper half of the torso axis, never a full hidden torso.
        lower = [[float(s.x + 0.5 * (hip.x - s.x)), float(s.y + 0.5 * (hip.y - s.y))]
                 for s, hip in zip(shoulders, hips)]
        polygon = [[float(p.x), float(p.y)] for p in shoulders] + [lower[1], lower[0]]
        visibility = min(float(p.visibility or 0) for p in shoulders)
        presence = min(float(p.presence or 0) for p in shoulders)
        mask = (result.segmentation_masks[0].numpy_view().copy()
                if result.segmentation_masks else None)
        return {'reason': None, 'polygon': polygon, 'visibility': visibility,
                'presence': presence, 'person_mask': mask, 'region': 'upper_torso',
                'hip_visibility': min(float(p.visibility or 0) for p in hips),
                'upper_torso_inferred_from_landmarks': True}


def box_from_polygon(polygon: list) -> list[float]:
    points = np.array(polygon)
    lo, hi = points.min(axis=0), points.max(axis=0)
    return [float(lo[0]), float(lo[1]), float(hi[0] - lo[0]), float(hi[1] - lo[1])]


def map_crop(reference_polygon: list, crop: list, candidate_polygon: list) -> list:
    """Transfer the user's selection in torso coordinates, not screen coordinates."""
    src = np.float32(reference_polygon)
    dst = np.float32(candidate_polygon)
    transform = cv2.getPerspectiveTransform(src, dst)
    x, y, w, h = crop
    points = np.float32([[[x, y], [x + w, y], [x + w, y + h], [x, y + h]]])
    mapped = cv2.perspectiveTransform(points, transform)[0]
    return mapped.astype(float).tolist()
