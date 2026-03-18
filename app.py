import streamlit as st
import torch
import numpy as np
from transformers import Swin2SRForImageSuperResolution, Swin2SRImageProcessor
from diffusers import AutoPipelineForText2Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image, ImageFilter
from github import Github, Auth
import datetime
import io
from googletrans import Translator

st.set_page_config(page_title="Đa Phương Tiện", layout="wide")
st.title(" Hệ thống AI Đa Phương Tiện")

# --- CẤU HÌNH HỆ THỐNG ---
GITHUB_TOKEN = "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"
REPO_NAME = "Dra-Dra04/DaPhuongTien"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def translate_text(text, target_lang='en'):
    try:
        translator = Translator()
        return translator.translate(text, dest=target_lang).text
    except:
        return text


# --- TẢI MÔ HÌNH TỐI ƯU ---
@st.cache_resource
def load_models():
    st.info("🚀 Đang khởi động AI")

    # 1. Sinh ảnh siêu tốc (SD-Turbo)
    pipe = AutoPipelineForText2Image.from_pretrained(
        "stabilityai/sd-turbo",
        torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
        variant="fp16" if DEVICE == "cuda" else None
    ).to(DEVICE)

    if DEVICE == "cuda":
        pipe.enable_attention_slicing()

    # 2. Mô tả ảnh (BLIP)
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(DEVICE)

    # 3. Làm nét ảnh siêu nhẹ
    upscale_processor = Swin2SRImageProcessor()
    upscale_model = Swin2SRForImageSuperResolution.from_pretrained("caidas/swin2SR-classical-sr-x2-64").to(DEVICE)
    return pipe, processor, model, upscale_processor, upscale_model


# --- HÀM TẢI LÊN GITHUB ---
def upload_to_github(image_bytes):
    if not GITHUB_TOKEN or GITHUB_TOKEN == "YOUR_TOKEN_HERE":
        return False, "Token chưa chính xác."
    try:
        auth = Auth.Token(GITHUB_TOKEN)
        g = Github(auth=auth)
        repo = g.get_repo(REPO_NAME)
        time_stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = f"generated_images/ai_img_{time_stamp}.png"
        repo.create_file(file_path, f"AI upload {time_stamp}", image_bytes, branch="main")
        return True, file_path
    except Exception as e:
        return False, str(e)


# --- GIAO DIỆN ---
txt2img_pipe, caption_processor, caption_model, upscale_processor, upscale_model = load_models()

tab1, tab2, tab3 = st.tabs(["✨ Sinh ảnh", "🔍 Mô tả ảnh", "🎨 Khử nhiễu & Làm nét"])

# --- TAB 1: SINH ẢNH SIÊU TỐC ---
with tab1:
    prompt_input = st.text_area("Mô tả hình ảnh:", placeholder="Ví dụ: Một phi hành gia...")
    if st.button("Tạo ảnh"):
        if prompt_input:
            with st.spinner("Đang vẽ..."):
                en_prompt = translate_text(prompt_input, 'en')
                output = txt2img_pipe(prompt=en_prompt, num_inference_steps=2, guidance_scale=0.0).images[0]
                st.image(output, caption="Kết quả (Cố định khung)", width=512)

                buf = io.BytesIO()
                output.save(buf, format="PNG")
                byte_im = buf.getvalue()

                col1, col2 = st.columns([1, 3])
                with col1:
                    st.download_button("📥 Tải về", byte_im, "ai_img.png", "image/png")
                with col2:
                    success, result = upload_to_github(byte_im)
                    if success:
                        st.success(f"☁️ GitHub: {result}")
                    else:
                        st.error(f"Lỗi: {result}")

# --- TAB 2: MÔ TẢ ẢNH ---
with tab2:
    up_file = st.file_uploader("Tải ảnh để AI đọc...", type=["jpg", "png"], key="tab2")
    if up_file:
        img = Image.open(up_file).convert('RGB')
        st.image(img, width=400)
        if st.button("Phân tích"):
            inputs = caption_processor(img, return_tensors="pt").to(DEVICE)
            out = caption_model.generate(**inputs)
            st.write(
                f"🇻🇳 **Kết quả:** {translate_text(caption_processor.decode(out[0], skip_special_tokens=True), 'vi')}")

# --- TAB 3: KHỬ NHIỄU & LÀM NÉT ---
with tab3:
    st.subheader(" Nâng cấp chất lượng hình ảnh bằng AI (Swin2SR Siêu Nhẹ)")
    up_noise = st.file_uploader("Tải ảnh cần làm nét...", type=["jpg", "png"], key="tab3")

    if up_noise:
        img_noise = Image.open(up_noise).convert('RGB')
        max_size = 512
        img_noise.thumbnail((max_size, max_size))

        w, h = img_noise.size

        col_a, col_b = st.columns(2)
        with col_a:
            st.image(img_noise, caption=f"Ảnh đầu vào ({w}x{h})", width=400)

        if st.button("Bắt đầu xử lý làm nét"):
            with st.spinner("AI đang tăng độ phân giải (chỉ mất vài giây)..."):
                # --- Sử dụng logic của Swin2SR thay vì Stable Diffusion ---
                inputs = upscale_processor(img_noise, return_tensors="pt").to(DEVICE)

                # Vô hiệu hóa gradient để tránh tràn RAM
                with torch.no_grad():
                    outputs = upscale_model(**inputs)

                # Dịch ngược kết quả AI thành ảnh
                output_tensor = outputs.reconstruction.data.squeeze().float().cpu().clamp_(0, 1).numpy()
                output_array = (np.moveaxis(output_tensor, 0, -1) * 255.0).round().astype(np.uint8)
                final_img = Image.fromarray(output_array)
                # ----------------------------------------------------------------------

                if DEVICE == "cuda":
                    torch.cuda.empty_cache()

                with col_b:
                    wf, hf = final_img.size
                    st.image(final_img, caption=f"Ảnh AI Enhanced ({wf}x{hf})", width=400)

                    buf_dn = io.BytesIO()
                    final_img.save(buf_dn, format="PNG")
                    st.download_button(
                        label="📥 Tải ảnh chất lượng cao",
                        data=buf_dn.getvalue(),
                        file_name="ai_upscaled_fast.png",
                        mime="image/png"
                    )

st.divider()