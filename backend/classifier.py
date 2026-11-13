"""
NutriLens AI — Food Classifier Implementation
Implements FoodModelInterface using PyTorch (MobileNetV2 or ResNet50 backbone).
"""

import os
import json
from typing import List, Optional, Dict, Any
from PIL import Image

import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms

from backend.base_model import FoodModelInterface, PredictionResult


class FoodClassifier(FoodModelInterface):
    """
    Image classification model for authentic Indian food items.
    Trained on 43 classes using transfer learning.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        class_names_path: Optional[str] = None,
        architecture: str = "mobilenet_v2",
        device: Optional[str] = None
    ):
        self.architecture = architecture.lower()
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[nn.Module] = None
        self.classes: List[str] = []
        self.class_to_idx: Dict[str, int] = {}
        self.idx_to_class: Dict[int, str] = {}
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

        if class_names_path and os.path.exists(class_names_path):
            self._load_classes(class_names_path)

        if model_path and os.path.exists(model_path):
            self.load(model_path, self.device)

    def _load_classes(self, class_names_path: str) -> None:
        with open(class_names_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and "classes" in data:
                self.classes = data["classes"]
                self.class_to_idx = data.get("class_to_idx", {c: i for i, c in enumerate(self.classes)})
                self.idx_to_class = {int(k): v for k, v in data.get("idx_to_class", {i: c for i, c in enumerate(self.classes)}).items()}
            elif isinstance(data, list):
                self.classes = data
                self.class_to_idx = {c: i for i, c in enumerate(self.classes)}
                self.idx_to_class = {i: c for i, c in enumerate(self.classes)}

    def _build_model(self, num_classes: int) -> nn.Module:
        """Construct the base model and replace classification head."""
        if self.architecture == "mobilenet_v2":
            model = models.mobilenet_v2(weights=None)
            in_features = model.classifier[1].in_features
            model.classifier = nn.Sequential(
                nn.Dropout(p=0.3),
                nn.Linear(in_features, num_classes)
            )
        elif self.architecture == "resnet50":
            model = models.resnet50(weights=None)
            in_features = model.fc.in_features
            model.fc = nn.Sequential(
                nn.Dropout(p=0.3),
                nn.Linear(in_features, num_classes)
            )
        else:
            raise ValueError(f"Unsupported architecture: {self.architecture}. Use 'mobilenet_v2' or 'resnet50'.")

        return model

    def load(self, model_path: str, device: Optional[str] = None) -> None:
        """Load trained model weights."""
        if device:
            self.device = device

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model checkpoint not found at: {model_path}")

        checkpoint = torch.load(model_path, map_location=self.device)

        # Check if checkpoint contains architecture metadata
        if isinstance(checkpoint, dict) and "architecture" in checkpoint:
            self.architecture = checkpoint["architecture"].lower()

        # Check if classes are stored in checkpoint
        if isinstance(checkpoint, dict) and "classes" in checkpoint and not self.classes:
            self.classes = checkpoint["classes"]
            self.class_to_idx = {c: i for i, c in enumerate(self.classes)}
            self.idx_to_class = {i: c for i, c in enumerate(self.classes)}

        num_classes = len(self.classes) if self.classes else 43
        self.model = self._build_model(num_classes)

        if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
            self.model.load_state_dict(checkpoint["state_dict"])
        elif isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            self.model.load_state_dict(checkpoint["model_state_dict"])
        elif isinstance(checkpoint, nn.Module):
            self.model = checkpoint
        else:
            self.model.load_state_dict(checkpoint)

        self.model.to(self.device)
        self.model.eval()

    def predict(self, image: Image.Image, conf_threshold: float = 0.15) -> List[PredictionResult]:
        """Classify the food in the provided image."""
        if self.model is None:
            raise RuntimeError("Model is not loaded. Call load() with valid weights first.")

        # Ensure image is RGB
        if image.mode != "RGB":
            image = image.convert("RGB")

        tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(tensor)
            probs = torch.softmax(outputs, dim=1).squeeze(0)

        # Get top predictions
        top_k_vals, top_k_indices = torch.topk(probs, k=min(5, len(probs)))
        top_k_vals = top_k_vals.cpu().tolist()
        top_k_indices = top_k_indices.cpu().tolist()

        best_idx = top_k_indices[0]
        best_prob = top_k_vals[0]
        food_name = self.idx_to_class.get(best_idx, f"class_{best_idx}")

        top_k_list = [
            {
                "food_name": self.idx_to_class.get(idx, f"class_{idx}"),
                "confidence": round(prob, 4),
                "class_id": idx
            }
            for prob, idx in zip(top_k_vals, top_k_indices)
        ]

        # For a full-image classification, box covers whole image: [0, 0, width, height]
        w, h = image.size
        return [PredictionResult(
            food_name=food_name,
            confidence=float(best_prob),
            class_id=int(best_idx),
            box=[0, 0, w, h],
            top_k=top_k_list
        )]

    def predict_region(self, image: Image.Image, box: List[int]) -> PredictionResult:
        """Crop the bounding box region and classify it."""
        x1, y1, x2, y2 = box
        # Validate coordinates
        w, h = image.size
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        if x2 <= x1 or y2 <= y1:
            raise ValueError(f"Invalid crop box dimensions: {box}")

        cropped_img = image.crop((x1, y1, x2, y2))
        preds = self.predict(cropped_img)
        res = preds[0]
        res.box = [int(x1), int(y1), int(x2), int(y2)]
        return res

    @staticmethod
    def _box_iou(a: List[int], b: List[int]) -> float:
        ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
        ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
        inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
        if inter <= 0:
            return 0.0
        area_a = max(0, a[2] - a[0]) * max(0, a[3] - a[1])
        area_b = max(0, b[2] - b[0]) * max(0, b[3] - b[1])
        union = area_a + area_b - inter
        return inter / union if union > 0 else 0.0

    def _propose_food_regions(self, image: Image.Image) -> List[List[int]]:
        """Generate candidate dish bounding boxes for multi-item plate/thali images."""
        w, h = image.size
        boxes: List[List[int]] = []

        try:
            import cv2
            import numpy as np

            np_img = np.array(image)
            small = cv2.resize(np_img, (256, 256))
            lab = cv2.cvtColor(small, cv2.COLOR_RGB2LAB).astype(np.float32)
            Z = lab.reshape((-1, 3))
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            _, labels, _ = cv2.kmeans(Z, 7, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
            label_img = labels.reshape((256, 256))

            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
            for k in range(7):
                mask = (label_img == k).astype(np.uint8) * 255
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                num_cc, _, stats, _ = cv2.connectedComponentsWithStats(mask)
                for c_id in range(1, num_cc):
                    x, y, bw, bh, area = stats[c_id]
                    area_ratio = area / (256 * 256)
                    if 0.04 <= area_ratio <= 0.40:
                        x1 = max(0, int(x / 256 * w) - int(0.02 * w))
                        y1 = max(0, int(y / 256 * h) - int(0.02 * h))
                        x2 = min(w, int((x + bw) / 256 * w) + int(0.02 * w))
                        y2 = min(h, int((y + bh) / 256 * h) + int(0.02 * h))
                        boxes.append([x1, y1, x2, y2])
        except Exception:
            pass

        # Structured overlapping plate tiles + center bowl region
        for rows, cols in [(2, 2), (2, 3), (3, 2)]:
            for r in range(rows):
                for c in range(cols):
                    boxes.append([
                        int(c * w / cols),
                        int(r * h / rows),
                        int((c + 1) * w / cols),
                        int((r + 1) * h / rows),
                    ])
        boxes.append([int(0.25 * w), int(0.25 * h), int(0.75 * w), int(0.75 * h)])

        unique_boxes: List[List[int]] = []
        for b in boxes:
            bw, bh = b[2] - b[0], b[3] - b[1]
            ar = bw / bh if bh > 0 else 0.0
            if bw >= w * 0.18 and bh >= h * 0.18 and 0.45 <= ar <= 2.2:
                if not any(self._box_iou(b, ub) > 0.72 for ub in unique_boxes):
                    unique_boxes.append(b)

        return unique_boxes or [[0, 0, w, h]]

    def predict_multi(
        self,
        image: Image.Image,
        conf_threshold: float = 0.40,
        max_items: int = 6
    ) -> List[PredictionResult]:
        """Detect and classify multiple dishes present in a single plate/thali image."""
        if self.model is None:
            raise RuntimeError("Model is not loaded. Call load() with valid weights first.")

        if image.mode != "RGB":
            image = image.convert("RGB")

        candidate_boxes = self._propose_food_regions(image)
        tensors = torch.stack([self.transform(image.crop(tuple(b))) for b in candidate_boxes]).to(self.device)

        with torch.no_grad():
            outputs = self.model(tensors)
            probs = torch.softmax(outputs, dim=1)

        k_count = min(5, probs.shape[1])
        top_k_vals, top_k_indices = torch.topk(probs, k=k_count, dim=1)
        top_k_vals = top_k_vals.cpu().tolist()
        top_k_indices = top_k_indices.cpu().tolist()

        candidates: List[PredictionResult] = []
        for box, vals, idxs in zip(candidate_boxes, top_k_vals, top_k_indices):
            best_idx = idxs[0]
            best_prob = float(vals[0])
            food_name = self.idx_to_class.get(best_idx, f"class_{best_idx}")
            top_k_list = [
                {
                    "food_name": self.idx_to_class.get(idx, f"class_{idx}"),
                    "confidence": round(float(prob), 4),
                    "class_id": int(idx)
                }
                for prob, idx in zip(vals, idxs)
            ]
            candidates.append(PredictionResult(
                food_name=food_name,
                confidence=best_prob,
                class_id=int(best_idx),
                box=box,
                top_k=top_k_list
            ))

        candidates.sort(key=lambda r: -r.confidence)

        selected: List[PredictionResult] = []
        seen_classes = set()
        for res in candidates:
            if res.confidence < conf_threshold and len(selected) >= 2:
                break
            if res.food_name in seen_classes:
                continue
            if any(self._box_iou(res.box, s.box) > 0.45 for s in selected if res.box and s.box):
                continue
            selected.append(res)
            seen_classes.add(res.food_name)
            if len(selected) >= max_items:
                break

        return selected or self.predict(image)

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_type": "image_classification",
            "architecture": self.architecture,
            "device": self.device,
            "num_classes": len(self.classes),
            "classes": self.classes,
            "is_loaded": self.model is not None
        }
