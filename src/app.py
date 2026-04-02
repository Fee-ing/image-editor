# file: /Users/BGZB002/Documents/Code/image-editor/src/app.py

import streamlit as st
from PIL import Image
import sys
import os
import io

# 导入我们的编辑逻辑
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
from editor import ImageEditor

# 导入画布组件
from streamlit_drawable_canvas import st_canvas

# --- 页面配置 ---
st.set_page_config(
    page_title="AI 图片编辑器",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 自定义 CSS (让界面更时尚简约) ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
    }
    .main-header {
        font-size: 2.5rem;
        color: #4A4A4A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- 侧边栏控制区 ---
with st.sidebar:
    st.header("🛠️ 工具箱")
    
    uploaded_file = st.file_uploader("上传本地图片", type=["jpg", "jpeg", "png"])
    
    st.divider()
    
    # 功能选择
    mode = st.radio("选择功能", ["智能去水印", "清晰化", "压缩", "裁剪"])
    
    # 智能去水印专属：选区绘制
    canvas_result = None
    stroke_width = 10
    stroke_color = "#ff0000"
    
    if mode == "智能去水印" and uploaded_file:
        st.markdown("### 🖌️ 绘制水印区域")
        st.info("💡 用鼠标框选需要去除的水印或字幕区域")
        
        # 加载图片获取尺寸
        temp_img = Image.open(uploaded_file)
        img_width, img_height = temp_img.size
        
        # 限制画布最大尺寸
        max_size = 600
        if img_width > max_size or img_height > max_size:
            scale = max_size / max(img_width, img_height)
            canvas_width = int(img_width * scale)
            canvas_height = int(img_height * scale)
        else:
            canvas_width = img_width
            canvas_height = img_height
        
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            background_image=temp_img,
            update_streamlit=True,
            height=canvas_height,
            width=canvas_width,
            drawing_mode="rect",
            key="canvas",
            display_toolbar=True
        )
        
        st.markdown("### 📐 选区设置")
        stroke_width = st.slider("画笔粗细", 5, 30, 10)
    
    # 其他功能的参数设置
    elif mode == "清晰化":
        sharpness = st.slider("锐化强度", 1.0, 3.0, 1.5)
    
    elif mode == "压缩":
        quality = st.slider("压缩质量 (1-100)", 10, 100, 60)
    
    elif mode == "裁剪":
        crop_method = st.selectbox("裁剪方式", ["中心裁剪", "自定义比例"])
        if crop_method == "自定义比例":
            crop_ratio = st.slider("保留比例 (%)", 50, 95, 80)
    
    st.divider()
    
    apply_btn = st.button("开始处理", type="primary", use_container_width=True)
    
    # 使用提示
    st.markdown("### 💡 使用提示")
    st.markdown("""
    - **智能去水印**: 框选水印区域后点击处理
    - **清晰化**: 调整锐化强度增强细节
    - **压缩**: 降低质量减小文件大小
    - **裁剪**: 移除图片边缘区域
    """)

# --- 主界面 ---
st.markdown('<p class="main-header">✨ 极简图片处理工具</p>', unsafe_allow_html=True)

if uploaded_file is not None:
    # 加载图片
    original_image = Image.open(uploaded_file)
    
    # 获取图片尺寸信息
    st.markdown(f"""
    <div class="info-box">
        📊 图片信息：{original_image.width} × {original_image.height} 像素 | 
        格式：{original_image.format} | 
        模式：{original_image.mode}
    </div>
    """, unsafe_allow_html=True)
    
    # 使用两列布局：左边原图，右边结果
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🖼️ 原图")
        st.image(original_image, use_column_width=True)

    with col2:
        st.subheader("✨ 处理结果")
        
        if apply_btn:
            with st.spinner('🔄 正在处理中...'):
                editor = ImageEditor()
                result_image = None
                
                try:
                    if mode == "智能去水印":
                        if canvas_result and canvas_result.objects:
                            # 计算画布与实际图片的比例
                            if canvas_result.height and canvas_result.width:
                                scale_y = original_image.height / canvas_result.height
                                scale_x = original_image.width / canvas_result.width
                                
                                # 提取所有矩形选区
                                boxes = []
                                for obj in canvas_result.objects:
                                    if obj["type"] == "rect":
                                        left = obj["left"] * scale_x
                                        top = obj["top"] * scale_y
                                        width = obj["width"] * scale_x
                                        height = obj["height"] * scale_y
                                        box = (left, top, left + width, top + height)
                                        boxes.append(box)
                                
                                # 处理第一个选区（或合并多个选区）
                                if boxes:
                                    # 合并所有选区为一个 bounding box
                                    all_left = min(b[0] for b in boxes)
                                    all_top = min(b[1] for b in boxes)
                                    all_right = max(b[2] for b in boxes)
                                    all_bottom = max(b[3] for b in boxes)
                                    merged_box = (all_left, all_top, all_right, all_bottom)
                                    
                                    result_image = editor.remove_watermark(original_image, merged_box)
                                    st.success(f"✅ 水印已去除 (处理区域：{len(boxes)} 个选区)")
                                else:
                                    st.warning("⚠️ 未检测到有效选区，使用自动检测模式")
                                    result_image = editor.remove_watermark(original_image)
                            else:
                                st.warning("⚠️ 画布尺寸异常，使用自动检测模式")
                                result_image = editor.remove_watermark(original_image)
                        else:
                            st.warning("⚠️ 未绘制选区，使用自动检测模式")
                            result_image = editor.remove_watermark(original_image)
                        
                    elif mode == "清晰化":
                        result_image = editor.sharpen(original_image, sharpness)
                        st.success(f"✅ 图片已清晰化 (强度：{sharpness})")
                        
                    elif mode == "压缩":
                        result_image = editor.compress(original_image, quality)
                        # 计算压缩率
                        original_size = uploaded_file.size
                        buf = io.BytesIO()
                        if result_image.mode in ("RGBA", "P"):
                            result_image = result_image.convert("RGB")
                        result_image.save(buf, format="JPEG")
                        compressed_size = len(buf.getvalue())
                        compression_rate = (1 - compressed_size / original_size) * 100
                        st.success(f"✅ 图片已压缩 (质量：{quality} | 压缩率：{compression_rate:.1f}%)")
                        
                    elif mode == "裁剪":
                        w, h = original_image.size
                        if crop_method == "中心裁剪":
                            ratio = 0.1
                        else:
                            ratio = (100 - crop_ratio) / 200
                        box = (w*ratio, h*ratio, w*(1-ratio), h*(1-ratio))
                        result_image = editor.crop(original_image, box)
                        st.success("✅ 图片已裁剪")

                    # 显示结果
                    if result_image:
                        st.image(result_image, use_column_width=True)
                        
                        # 提供下载按钮
                        buf = io.BytesIO()
                        if result_image.mode in ("RGBA", "P"):
                            result_image = result_image.convert("RGB")
                        result_image.save(buf, format="JPEG")
                        byte_im = buf.getvalue()
                        
                        st.download_button(
                            label="⬇️ 下载处理后的图片",
                            data=byte_im,
                            file_name="processed_image.jpg",
                            mime="image/jpeg",
                            use_container_width=True
                        )
                        
                except Exception as e:
                    st.error(f"❌ 处理出错：{str(e)}")
                    st.exception(e)
        else:
            st.info("👈 请在左侧选择功能并点击「开始处理」")

else:
    st.info("👆 请在左侧侧边栏上传图片开始体验")

# --- 底部功能说明 ---
st.divider()
st.markdown("""
### 📖 功能说明

| 功能 | 描述 | 适用场景 |
|------|------|----------|
| 🧹 智能去水印 | AI 自动识别并去除水印/字幕 | 去除图片水印、文字遮挡 |
| 🔍 清晰化 | 增强图片边缘和细节 | 模糊图片变清晰 |
| 📦 压缩 | 减小图片文件大小 | 节省存储空间、加快加载 |
| ✂️ 裁剪 | 移除图片边缘区域 | 调整构图、去除多余部分 |

---
**Powered by AI Image Editor** | 基于深度学习图像修复技术
""")