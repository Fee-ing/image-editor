# file: /Users/BGZB002/Documents/Code/image-editor/src/editor.py

import cv2
import numpy as np
from PIL import Image
from typing import Optional, Tuple


class ImageEditor:
    """图片编辑器类（轻量版，无需深度学习依赖）"""
    
    def __init__(self):
        """初始化编辑器"""
        pass
    
    def remove_watermark(self, image: Image.Image, box: Optional[Tuple] = None) -> Image.Image:
        """
        智能去水印/字幕（使用 OpenCV 传统算法）
        
        参数:
            image: PIL 图片对象
            box: 选区坐标 (left, top, right, bottom)，可选
            
        返回:
            处理后的 PIL 图片对象
        """
        img_array = np.array(image.convert("RGB"))
        
        if box:
            mask = self._create_mask(img_array.shape[:2], box)
            result = self._traditional_inpaint(img_array, mask)
        else:
            mask = self._detect_watermark_area(img_array)
            result = self._traditional_inpaint(img_array, mask)
        
        return Image.fromarray(result)
    
    def _create_mask(self, shape: Tuple, box: Tuple) -> np.ndarray:
        """根据选区创建掩码"""
        mask = np.zeros(shape, dtype=np.uint8)
        left, top, right, bottom = map(int, box)
        
        left = max(0, left)
        top = max(0, top)
        right = min(shape[1], right)
        bottom = min(shape[0], bottom)
        
        mask[top:bottom, left:right] = 255
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        
        return mask
    
    def _detect_watermark_area(self, img_array: np.ndarray) -> np.ndarray:
        """自动检测水印区域"""
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        h, w = dilated.shape
        edge_mask = np.zeros_like(dilated)
        edge_margin = int(h * 0.15)
        edge_mask[:edge_margin, :] = 255
        edge_mask[-edge_margin:, :] = 255
        edge_mask[:, :edge_margin] = 255
        edge_mask[:, -edge_margin:] = 255
        
        mask = cv2.bitwise_and(dilated, dilated, mask=edge_mask)
        
        return mask
    
    def _traditional_inpaint(self, img_array: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """传统图像修复算法"""
        result1 = cv2.inpaint(img_array, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
        result2 = cv2.inpaint(img_array, mask, inpaintRadius=5, flags=cv2.INPAINT_NS)
        result = cv2.addWeighted(result1, 0.5, result2, 0.5, 0)
        result = cv2.GaussianBlur(result, (3, 3), 0)
        
        return result
    
    def sharpen(self, image: Image.Image, sharpness: float) -> Image.Image:
        """图片清晰化/锐化"""
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(sharpness)
    
    def compress(self, image: Image.Image, quality: int) -> Image.Image:
        """图片压缩"""
        buf = io.BytesIO()
        
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        
        image.save(buf, format="JPEG", quality=quality, optimize=True)
        buf.seek(0)
        
        return Image.open(buf)
    
    def crop(self, image: Image.Image, box: Tuple) -> Image.Image:
        """图片裁剪"""
        return image.crop(box)