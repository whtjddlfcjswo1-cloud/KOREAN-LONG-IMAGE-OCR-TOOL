"""Image preprocessing and enhancement utilities for low-confidence OCR retry."""

import hashlib
from typing import List, Tuple
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


def compute_file_hash(filepath: str) -> str:
    """Computes SHA-256 hash of a file."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def compute_image_hash(image_bytes: bytes) -> str:
    """Computes SHA-256 hash of image bytes."""
    return hashlib.sha256(image_bytes).hexdigest()


def crop_with_padding(image: Image.Image, bbox: List[float], padding: int = 30) -> Tuple[Image.Image, Tuple[int, int]]:
    """Crops a bounding box with safety padding from the full-resolution image."""
    if len(bbox) == 4 and isinstance(bbox[0], (int, float)):
        x1, y1, x2, y2 = bbox
    elif len(bbox) == 4 and isinstance(bbox[0], (list, tuple)):
        xs = [pt[0] for pt in bbox]
        ys = [pt[1] for pt in bbox]
        x1, x2 = min(xs), max(xs)
        y1, y2 = min(ys), max(ys)
    else:
        raise ValueError(f"Unrecognized bbox format: {bbox}")
    w, h = image.size
    px1 = max(0, int(x1) - padding)
    py1 = max(0, int(y1) - padding)
    px2 = min(w, int(x2) + padding)
    py2 = min(h, int(y2) + padding)
    return image.crop((px1, py1, px2, py2)), (px1, py1)


def enhance_upscale(image: Image.Image, factor: float = 1.5) -> Image.Image:
    nw = int(image.width * factor)
    nh = int(image.height * factor)
    return image.resize((nw, nh), resample=Image.Resampling.LANCZOS)


def enhance_contrast(image: Image.Image) -> Image.Image:
    np_img = np.array(image.convert("RGB"))
    lab = cv2.cvtColor(np_img, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    return Image.fromarray(cv2.cvtColor(cv2.merge((cl, a, b)), cv2.COLOR_LAB2RGB))


def enhance_sharpen(image: Image.Image) -> Image.Image:
    np_img = np.array(image.convert("L"))
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]], dtype=np.float32)
    return Image.fromarray(cv2.filter2D(np_img, -1, kernel)).convert("RGB")


def enhance_adaptive_threshold(image: Image.Image) -> Image.Image:
    np_img = np.array(image.convert("L"))
    binarized = cv2.adaptiveThreshold(np_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 6)
    return Image.fromarray(binarized).convert("RGB")


def get_preprocessing_variants(image: Image.Image, upscale_factor: float = 1.5) -> List[Tuple[str, Image.Image]]:
    variants = [("native", image)]
    up = enhance_upscale(image, factor=upscale_factor)
    variants.append(("upscaled", up))
    try:
        variants.append(("contrast", enhance_contrast(up)))
    except Exception:
        pass
    try:
        variants.append(("sharpened", enhance_sharpen(up)))
    except Exception:
        pass
    try:
        variants.append(("adaptive_threshold", enhance_adaptive_threshold(up)))
    except Exception:
        pass
    return variants
