# file: /Users/BGZB002/Documents/Code/image-editor/src/editor.py

import cv2
import numpy as np
from PIL import Image
from typing import Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F


class ImageEditor:
    """
    图片编辑器类，提供多种图片处理功能
    """
    
    def __init__(self):
        """
        初始化编辑器，加载深度学习模型
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.inpaint_model = self._load_inpaint_model()
    
    def _load_inpaint_model(self) -> nn.Module:
        """
        加载图像修复深度学习模型
        
        返回:
            加载的模型对象
        """
        # 使用简化的 U-Net 架构作为 inpainting 模型
        model = SimpleInpaintNet().to(self.device)
        model.eval()
        return model
    
    def remove_watermark(self, image: Image.Image, box: Optional[Tuple] = None) -> Image.Image:
        """
        智能去水印/字幕
        
        参数:
            image: PIL 图片对象
            box: 选区坐标 (left, top, right, bottom)，可选。如果不传则尝试自动检测
            
        返回:
            处理后的 PIL 图片对象
        """
        img_array = np.array(image.convert("RGB"))
        
        if box:
            # 用户指定选区
            mask = self._create_mask(img_array.shape[:2], box)
            result = self._ai_inpaint(img_array, mask)
        else:
            # 自动检测水印区域
            mask = self._detect_watermark_area(img_array)
            result = self._ai_inpaint(img_array, mask)
        
        return Image.fromarray(result)
    
    def _create_mask(self, shape: Tuple, box: Tuple) -> np.ndarray:
        """
        根据选区创建掩码
        
        参数:
            shape: 图片形状 (height, width)
            box: 选区坐标 (left, top, right, bottom)
            
        返回:
            二值掩码数组
        """
        mask = np.zeros(shape, dtype=np.uint8)
        left, top, right, bottom = map(int, box)
        
        # 确保坐标在图片范围内
        left = max(0, left)
        top = max(0, top)
        right = min(shape[1], right)
        bottom = min(shape[0], bottom)
        
        mask[top:bottom, left:right] = 255
        
        # 边缘羽化，使修复更自然
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        
        return mask
    
    def _detect_watermark_area(self, img_array: np.ndarray) -> np.ndarray:
        """
        自动检测水印区域（基于边缘和纹理分析）
        
        参数:
            img_array: 图片 numpy 数组
            
        返回:
            检测到的水印区域掩码
        """
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # 1. 边缘检测
        edges = cv2.Canny(gray, 50, 150)
        
        # 2. 检测高频区域（水印通常有清晰的边缘）
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian = np.uint8(np.absolute(laplacian))
        
        # 3. 形态学操作
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # 4. 结合边缘和拉普拉斯结果
        mask = cv2.addWeighted(dilated, 0.7, laplacian, 0.3, 0)
        _, mask = cv2.threshold(mask, 50, 255, cv2.THRESH_BINARY)
        
        # 5. 只保留图片边缘区域（水印通常在角落）
        h, w = mask.shape
        edge_mask = np.zeros_like(mask)
        edge_margin = int(h * 0.15)
        edge_mask[:edge_margin, :] = 255
        edge_mask[-edge_margin:, :] = 255
        edge_mask[:, :edge_margin] = 255
        edge_mask[:, -edge_margin:] = 255
        
        mask = cv2.bitwise_and(mask, mask, mask=edge_mask)
        
        return mask
    
    def _ai_inpaint(self, img_array: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        使用 AI 模型进行图像修复
        
        参数:
            img_array: 图片 numpy 数组
            mask: 掩码数组
            
        返回:
            修复后的图片数组
        """
        # 预处理
        img_tensor = self._preprocess_image(img_array)
        mask_tensor = self._preprocess_mask(mask)
        
        # 使用深度学习模型修复
        with torch.no_grad():
            try:
                result_tensor = self.inpaint_model(img_tensor, mask_tensor)
                result_array = self._postprocess_image(result_tensor)
            except Exception as e:
                # 模型失败时使用传统算法 fallback
                print(f"AI 模型修复失败，使用传统算法：{e}")
                result_array = self._traditional_inpaint(img_array, mask)
        
        return result_array
    
    def _traditional_inpaint(self, img_array: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        传统图像修复算法（作为 fallback）
        
        参数:
            img_array: 图片 numpy 数组
            mask: 掩码数组
            
        返回:
            修复后的图片数组
        """
        # 多算法融合
        result1 = cv2.inpaint(img_array, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
        result2 = cv2.inpaint(img_array, mask, inpaintRadius=5, flags=cv2.INPAINT_NS)
        
        # 融合结果
        result = cv2.addWeighted(result1, 0.5, result2, 0.5, 0)
        
        # 边缘平滑
        result = cv2.GaussianBlur(result, (3, 3), 0)
        
        return result
    
    def _preprocess_image(self, img_array: np.ndarray) -> torch.Tensor:
        """
        图片预处理，转换为模型输入格式
        
        参数:
            img_array: 图片 numpy 数组
            
        返回:
            预处理后的张量
        """
        img_tensor = torch.from_numpy(img_array).float() / 255.0
        img_tensor = img_tensor.permute(2, 0, 1).unsqueeze(0)  # (1, 3, H, W)
        return img_tensor.to(self.device)
    
    def _preprocess_mask(self, mask: np.ndarray) -> torch.Tensor:
        """
        掩码预处理
        
        参数:
            mask: 掩码数组
            
        返回:
            预处理后的张量
        """
        mask_tensor = torch.from_numpy(mask).float() / 255.0
        mask_tensor = mask_tensor.unsqueeze(0).unsqueeze(0)  # (1, 1, H, W)
        return mask_tensor.to(self.device)
    
    def _postprocess_image(self, tensor: torch.Tensor) -> np.ndarray:
        """
        模型输出后处理，转换回图片格式
        
        参数:
            tensor: 模型输出张量
            
        返回:
            处理后的 numpy 数组
        """
        tensor = tensor.squeeze(0).permute(1, 2, 0)
        tensor = torch.clamp(tensor, 0, 1)
        array = (tensor.cpu().numpy() * 255).astype(np.uint8)
        return array
    
    def sharpen(self, image: Image.Image, sharpness: float) -> Image.Image:
        """
        图片清晰化/锐化
        
        参数:
            image: PIL 图片对象
            sharpness: 锐化强度 (1.0-3.0)
            
        返回:
            处理后的 PIL 图片对象
        """
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(sharpness)
    
    def compress(self, image: Image.Image, quality: int) -> Image.Image:
        """
        图片压缩
        
        参数:
            image: PIL 图片对象
            quality: 压缩质量 (1-100)
            
        返回:
            处理后的 PIL 图片对象
        """
        import io
        buf = io.BytesIO()
        
        # 转换格式
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        
        image.save(buf, format="JPEG", quality=quality, optimize=True)
        buf.seek(0)
        
        return Image.open(buf)
    
    def crop(self, image: Image.Image, box: Tuple) -> Image.Image:
        """
        图片裁剪
        
        参数:
            image: PIL 图片对象
            box: 裁剪区域 (left, top, right, bottom)
            
        返回:
            处理后的 PIL 图片对象
        """
        return image.crop(box)


class SimpleInpaintNet(nn.Module):
    """
    简化的图像修复 U-Net 网络
    
    用于学习和修复被遮挡的图像区域
    """
    
    def __init__(self, in_channels: int = 4, out_channels: int = 3):
        """
        初始化网络
        
        参数:
            in_channels: 输入通道数 (3 通道图片 + 1 通道掩码)
            out_channels: 输出通道数
        """
        super(SimpleInpaintNet, self).__init__()
        
        # 编码器
        self.enc1 = self._downsample_block(in_channels, 64)
        self.enc2 = self._downsample_block(64, 128)
        self.enc3 = self._downsample_block(128, 256)
        self.enc4 = self._downsample_block(256, 512)
        
        # 瓶颈层
        self.bottleneck = self._residual_block(512, 512)
        
        # 解码器
        self.dec4 = self._upsample_block(512, 256)
        self.dec3 = self._upsample_block(256, 128)
        self.dec2 = self._upsample_block(128, 64)
        self.dec1 = self._upsample_block(64, 32)
        
        # 输出层
        self.output = nn.Sequential(
            nn.Conv2d(32, out_channels, kernel_size=3, padding=1),
            nn.Sigmoid()
        )
    
    def _downsample_block(self, in_ch: int, out_ch: int) -> nn.Sequential:
        """
        下采样块
        
        参数:
            in_ch: 输入通道数
            out_ch: 输出通道数
            
        返回:
            下采样模块
        """
        return nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2)
        )
    
    def _upsample_block(self, in_ch: int, out_ch: int) -> nn.Sequential:
        """
        上采样块
        
        参数:
            in_ch: 输入通道数
            out_ch: 输出通道数
            
        返回:
            上采样模块
        """
        return nn.Sequential(
            nn.ConvTranspose2d(in_ch, out_ch, kernel_size=2, stride=2),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
        )
    
    def _residual_block(self, in_ch: int, out_ch: int) -> nn.Sequential:
        """
        残差块
        
        参数:
            in_ch: 输入通道数
            out_ch: 输出通道数
            
        返回:
            残差模块
        """
        return nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
        )
    
    def forward(self, x: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        参数:
            x: 输入图片张量
            mask: 掩码张量
            
        返回:
            修复后的图片张量
        """
        # 拼接图片和掩码
        x = torch.cat([x, mask], dim=1)
        
        # 编码
        e1 = self.enc1(x)
        e2 = self.enc2(e1)
        e3 = self.enc3(e2)
        e4 = self.enc4(e3)
        
        # 瓶颈
        b = self.bottleneck(e4)
        
        # 解码
        d4 = self.dec4(b)
        d3 = self.dec3(d4)
        d2 = self.dec2(d3)
        d1 = self.dec1(d2)
        
        # 输出
        output = self.output(d1)
        
        # 只修复掩码区域
        output = output * mask + x[:, :3] * (1 - mask)
        
        return output