import cv2
import numpy as np

from backend.app.config import DEFAULT_CONFIG
from backend.app.analysis.quality import assess
from backend.app.analysis.wardrobe import histogram, distance
from backend.app.analysis.pose import map_crop


def test_blurred_visible_torso_is_unassessable_not_a_match():
    image = np.full((200, 200, 3), 100, np.uint8)
    polygon = [[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8]]
    reasons, _, _ = assess(image, {'visibility': 1, 'presence': 1}, polygon, DEFAULT_CONFIG)
    assert 'blurred' in reasons


def test_missing_correspondence_cannot_be_forced_by_manual_approval():
    reasons, _, mask = assess(np.zeros((200, 200, 3), np.uint8),
                              {'reason': 'torso_not_visible'}, None, DEFAULT_CONFIG)
    assert 'unreliable_correspondence' in reasons
    assert mask is None


def test_histogram_distance_is_measurement_not_canned_score():
    mask = np.full((100, 100), 255, np.uint8)
    red = np.full((100, 100, 3), [30, 30, 180], np.uint8)
    blue = np.full((100, 100, 3), [180, 30, 30], np.uint8)
    assert distance(histogram(red, mask, 16), histogram(red, mask, 16)) == 0
    assert distance(histogram(red, mask, 16), histogram(blue, mask, 16)) > 0.9


def test_crop_follows_translated_torso():
    ref = [[0.2, 0.2], [0.6, 0.2], [0.6, 0.7], [0.2, 0.7]]
    candidate = [[x + 0.1, y + 0.1] for x, y in ref]
    mapped = np.array(map_crop(ref, [0.2, 0.2, 0.4, 0.5], candidate))
    assert np.allclose(mapped, candidate)
