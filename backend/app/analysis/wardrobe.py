import cv2
import numpy as np


def histogram(image, mask, bins: int):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    hist = cv2.calcHist([lab], [1, 2], mask, [bins, bins], [0, 256, 0, 256])
    total = float(hist.sum())
    if total <= 0:
        raise ValueError('No assessable pixels')
    return (hist / total).astype(np.float32)


def distance(reference, candidate):
    return float(np.clip(cv2.compareHist(reference, candidate, cv2.HISTCMP_BHATTACHARYYA), 0, 1))
