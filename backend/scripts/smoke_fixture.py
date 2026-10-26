"""Controlled augmentation for state-machine checks, NOT wardrobe validation.

The source is an upstream real pose photograph. These are frozen, recoloured
fixtures; they must never be described as real changing-outfit video footage.
"""
import argparse
import subprocess
from pathlib import Path

import cv2
import numpy as np

from backend.app.analysis.pose import TorsoDetector
from backend.app.config import MODEL


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('image', type=Path)
    args = parser.parse_args()
    source = cv2.imread(str(args.image))
    detector = TorsoDetector(MODEL)
    try:
        pose = detector.detect(source)
    finally:
        detector.close()
    if not pose['polygon']:
        raise SystemExit('Source pose required for this controlled fixture')
    h, w = source.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    polygon = np.array(pose['polygon']) * [w, h]
    cv2.fillConvexPoly(mask, polygon.astype(np.int32), 255)
    folder = Path('data/smoke')
    folder.mkdir(parents=True, exist_ok=True)
    for index, chroma in enumerate([(180, 160), (70, 170), (160, 60)]):
        lab = cv2.cvtColor(source, cv2.COLOR_BGR2LAB)
        lab[:, :, 1][mask > 0] = chroma[0]
        lab[:, :, 2][mask > 0] = chroma[1]
        image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        still = folder / f'augmented-{index}.png'
        cv2.imwrite(str(still), image)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-i', str(still),
                        '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-t', '1', '-r', '4',
                        '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                        str(folder / f'augmented-{index}.mp4')], check=True)
    print('Created frozen recoloured fixtures, not real wardrobe validation footage.')


if __name__ == '__main__':
    main()
