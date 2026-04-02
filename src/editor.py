import cv2
import numpy as np
from PIL import Image, ImageEnhance

class ImageEditor:
    @staticmethod
    def remove_watermark(img_pil):
        """
        智能去水印/字幕
        策略：检测底部高亮区域（假设字幕是白色的）并修复
        """
        # 将 PIL 转为 OpenCV 格式 (RGB -> BGR)
        img = np.array(img_pil)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        h, w = img_bgr.shape[:2]
        
        # 创建一个掩膜
        mask = np.zeros((h, w), np.uint8)
        
        # 简单策略：假设水印在底部 15% 且颜色较浅
        # 实际项目中可以使用 AI 模型来生成更精准的 mask
        y_start = int(h * 0.85)
        roi = img_bgr[y_start:h, :]
        
        # 简单的阈值处理来检测白色/亮色文字
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        # 将检测到的区域映射回完整掩膜
        mask[y_start:h, :] = thresh
        
        # 膨胀掩膜，确保覆盖边缘
        kernel = np.ones((5,5),np.uint8)
        dilated_mask = cv2.dilate(mask, kernel, iterations=2)
        
        # 使用 Telea 算法修复
        result_bgr = cv2.inpaint(img_bgr, dilated_mask, 3, cv2.INPAINT_TELEA)
        
        # 转回 PIL (BGR -> RGB)
        result_rgb = cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB)
        return Image.fromarray(result_rgb)

    @staticmethod
    def sharpen(img_pil, amount=1.5):
        """
        图片清晰化 (锐化)
        """
        # 使用 PIL 的锐化增强
        enhancer = ImageEnhance.Sharpness(img_pil)
        return enhancer.enhance(amount)

    @staticmethod
    def compress(img_pil, quality=60):
        """
        压缩图片
        """
        # 创建一个字节流来模拟保存过程
        import io
        output = io.BytesIO()
        
        # 确保是 RGB 模式 (处理 PNG 透明通道问题)
        if img_pil.mode in ("RGBA", "P"):
            img_pil = img_pil.convert("RGB")
            
        img_pil.save(output, format="JPEG", quality=quality, optimize=True)
        
        # 重新加载以返回 PIL 对象（或者直接返回字节流用于下载）
        output.seek(0)
        return Image.open(output)

    @staticmethod
    def crop(img_pil, box):
        """
        裁剪
        box: (left, upper, right, lower)
        """
        return img_pil.crop(box)