# file: /Users/BGZB002/Documents/Code/image-editor/src/app.py

import streamlit as st
from PIL import Image
import io
import sys
import os

# 兼容本地和 Streamlit Cloud 部署
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from editor import ImageEditor

# --- 页面配置 ---
st.set_page_config(
    page_title="AI 图片编辑器",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 自定义 CSS ---
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
    .tip-box {
        background-color: #e7f3ff;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
        border-left: 4px solid #2196F3;
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
    
    # 智能去水印专属：坐标输入
    watermark_box = None
    use_auto_detect = True
    
    if mode == "智能去水印" and uploaded_file:
        st.markdown("### 📐 水印区域设置")
        
        temp_img = Image.open(uploaded_file)
        img_width, img_height = temp_img.size
        
        # 自动检测开关
        use_auto_detect = st.checkbox("✅ 自动检测水印区域", value=True)
        
        if not use_auto_detect:
            st.markdown(f"📊 图片尺寸：**{img_width} × {img_height}**")
            
            col1, col2 = st.columns(2)
            with col1:
                left = st.number_input("左边界", min_value=0, max_value=img_width, value=0)
                top = st.number_input("上边界", min_value=0, max_value=img_height, value=0)
            with col2:
                right = st.number_input("右边界", min_value=0, max_value=img_width, value=img_width//4)
                bottom = st.number_input("下边界", min_value=0, max_value=img_height, value=img_height//4)
            
            watermark_box = (left, top, right, bottom)
            
            st.markdown("""
            <div class="tip-box">
            💡 <strong>常用预设：</strong>
            <br>• 右下角水印：左=70%, 上=80%, 右=100%, 下=100%
            <br>• 底部字幕：左=0%, 上=90%, 右=100%, 下=100%
            <br>• 左上角水印：左=0%, 上=0%, 右=30%, 下=20%
            </div>
            """, unsafe_allow_html=True)
            
            # 快速预设按钮
            st.markdown("**🔧 快速预设：**")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("右下角"):
                    st.session_state.box = (img_width*0.7, img_height*0.8, img_width, img_height)
            with col_b:
                if st.button("底部字幕"):
                    st.session_state.box = (0, img_height*0.9, img_width, img_height)
            with col_c:
                if st.button("左上角"):
                    st.session_state.box = (0, 0, img_width*0.3, img_height*0.2)
            
            if 'box' in st.session_state:
                watermark_box = st.session_state.box
    
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
    - **智能去水印**: 自动检测或手动输入坐标
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
        📊 图片信息：**{original_image.width} × {original_image.height}** 像素 | 
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
                        if not use_auto_detect and watermark_box:
                            # 使用手动输入的坐标
                            result_image = editor.remove_watermark(original_image, watermark_box)
                            st.success(f"✅ 水印已去除 (手动坐标：{watermark_box})")
                        else:
                            # 自动检测
                            result_image = editor.remove_watermark(original_image)
                            st.info("🔍 使用自动检测模式")
                        
                    elif mode == "清晰化":
                        result_image = editor.sharpen(original_image, sharpness)
                        st.success(f"✅ 图片已清晰化 (强度：{sharpness})")
                        
                    elif mode == "压缩":
                        result_image = editor.compress(original_image, quality)
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
| 🧹 智能去水印 | 自动识别并去除水印/字幕 | 去除图片水印、文字遮挡 |
| 🔍 清晰化 | 增强图片边缘和细节 | 模糊图片变清晰 |
| 📦 压缩 | 减小图片文件大小 | 节省存储空间、加快加载 |
| ✂️ 裁剪 | 移除图片边缘区域 | 调整构图、去除多余部分 |

---
**Powered by AI Image Editor** | 基于 OpenCV 图像修复技术
""")