import streamlit as st
from PIL import Image
import sys
import os

# 导入我们的编辑逻辑
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
from editor import ImageEditor

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
</style>
""", unsafe_allow_html=True)

# --- 侧边栏控制区 ---
with st.sidebar:
    st.header("🛠️ 工具箱")
    
    uploaded_file = st.file_uploader("上传本地图片", type=["jpg", "jpeg", "png"])
    
    st.divider()
    
    # 功能选择
    mode = st.radio("选择功能", ["智能去水印", "清晰化", "压缩", "裁剪"])
    
    apply_btn = st.button("开始处理", type="primary")

# --- 主界面 ---
st.markdown('<p class="main-header">✨ 极简图片处理工具</p>', unsafe_allow_html=True)

if uploaded_file is not None:
    # 加载图片
    original_image = Image.open(uploaded_file)
    
    # 使用两列布局：左边原图，右边结果（或者使用对比滑块）
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("原图")
        st.image(original_image, use_column_width=True)

    with col2:
        st.subheader("处理结果")
        
        if apply_btn:
            with st.spinner('正在处理中...'):
                editor = ImageEditor()
                result_image = None
                
                try:
                    if mode == "智能去水印":
                        result_image = editor.remove_watermark(original_image)
                        st.success("✅ 水印/字幕已去除")
                        
                    elif mode == "清晰化":
                        # 这里可以加个滑块让用户控制强度
                        sharpness = st.slider("锐化强度", 1.0, 3.0, 1.5)
                        result_image = editor.sharpen(original_image, sharpness)
                        st.success("✅ 图片已清晰化")
                        
                    elif mode == "压缩":
                        quality = st.slider("压缩质量 (1-100)", 10, 100, 60)
                        result_image = editor.compress(original_image, quality)
                        st.success(f"✅ 图片已压缩 (质量: {quality})")
                        
                    elif mode == "裁剪":
                        # 简单的中心裁剪示例
                        w, h = original_image.size
                        box = (w*0.1, h*0.1, w*0.9, h*0.9) # 裁剪掉边缘 10%
                        result_image = editor.crop(original_image, box)
                        st.success("✅ 图片已裁剪")

                    # 显示结果
                    if result_image:
                        st.image(result_image, use_column_width=True)
                        
                        # 提供下载按钮
                        # 将 PIL 图片转换为字节流
                        import io
                        buf = io.BytesIO()
                        if result_image.mode in ("RGBA", "P"):
                            result_image = result_image.convert("RGB")
                        result_image.save(buf, format="JPEG")
                        byte_im = buf.getvalue()
                        
                        st.download_button(
                            label="⬇️ 下载处理后的图片",
                            data=byte_im,
                            file_name="processed_image.jpg",
                            mime="image/jpeg"
                        )
                        
                except Exception as e:
                    st.error(f"处理出错: {e}")
        else:
            st.info("👈 请在左侧选择功能并点击开始处理")

else:
    st.info("👆 请在左侧侧边栏上传图片开始体验")

# --- 底部对比展示 (可选) ---
if uploaded_file and apply_btn:
    st.divider()
    st.subheader("🔍 细节对比")
    # 使用 streamlit-image-comparison 组件
    # 注意：需要将 PIL 图片保存为临时文件或字节流传给组件
    # 这里为了简化，我们直接用两列布局展示，或者使用专门的对比组件
    # 如果你安装了 streamlit-image-comparison，可以用下面这行：
    # streamlit_image_comparison(original_image, result_image)

# 使用原生的双列布局
col1, col2 = st.columns(2)

with col1:
    st.subheader("🖼️ 原图")
    st.image(original_image, use_column_width=True)
    
with col2:
    st.subheader("✨ 处理后")
    if 'result_image' in locals(): # 假设你已经处理好了图片
        st.image(result_image, use_column_width=True)
    else:
        st.info("处理后的图片将显示在这里")