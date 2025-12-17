import streamlit as st
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import cv2
import tempfile
import numpy as np
import speech_recognition as sr
from PIL import Image

st.set_page_config(page_title="AI Clipper Pro — Gratis", layout="wide")
st.title("🤖 AI Clipper Pro — Gratis Tanpa Bayar")

uploaded_file = st.file_uploader("Upload Video", type=["mp4", "mov", "avi"])

if uploaded_file:
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_file.read())
    video_path = tfile.name

    clip = VideoFileClip(video_path)
    duration = clip.duration
    st.video(video_path)

    # Pilihan fitur
    st.subheader("🔧 Pengaturan AI Clipper")
    add_captions = st.checkbox("Tambahkan Caption Otomatis", value=False)
    reframe_to_vertical = st.checkbox("Ubah ke Format Vertikal (9:16)", value=True)
    add_logo = st.checkbox("Tambahkan Logo", value=False)
    logo_file = None
    if add_logo:
        logo_file = st.file_uploader("Upload Logo (PNG)", type=["png"])

    if st.button("✨ Buat Clip AI"):
        with st.spinner("Mendeteksi momen menarik..."):
            # Deteksi momen sederhana (wajah + perubahan frame)
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            moments = []

            for i in range(0, total_frames, int(fps * 3)):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if ret:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                    if len(faces) > 0:
                        start = i / fps
                        end = start + 5
                        moments.append((start, end))

            cap.release()

        st.success(f"Ditemukan {len(moments)} momen menarik!")

        for idx, (start, end) in enumerate(moments):
            subclip = clip.subclip(start, end)

            # 🔁 Reframe ke 9:16
            if reframe_to_vertical:
                h, w = subclip.size
                target_w = 1080
                target_h = 1920
                if w > h:
                    new_w = int(h * (target_w / target_h))
                    subclip = subclip.crop(x_center=w//2, width=new_w, height=h)
                subclip = subclip.resize((target_w, target_h))

            # 🗣️ Tambahkan caption otomatis
            if add_captions:
                try:
                    audio = subclip.audio
                    audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
                    audio.write_audiofile(audio_path, logger=None)

                    r = sr.Recognizer()
                    with sr.AudioFile(audio_path) as source:
                        audio_data = r.record(source)
                        text = r.recognize_google(audio_data, language="id-ID")  # Ganti ke bahasa kamu

                    txt_clip = TextClip(text, fontsize=50, color='white', font='Arial-Bold', bg_color='black')
                    txt_clip = txt_clip.set_position(('center', 'bottom')).set_duration(subclip.duration)
                    subclip = CompositeVideoClip([subclip, txt_clip.set_position(('center', 'bottom'))])
                except:
                    st.warning("Caption otomatis gagal (mungkin tidak ada suara).")

            # 🖼️ Tambahkan logo
            if add_logo and logo_file:
                logo = Image.open(logo_file)
                logo_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
                logo.save(logo_path)

                from moviepy.editor import ImageClip
                logo_clip = ImageClip(logo_path).set_duration(subclip.duration)
                logo_clip = logo_clip.resize(height=100)
                logo_clip = logo_clip.set_position(("right", "top"))

                subclip = CompositeVideoClip([subclip, logo_clip])

            # Simpan ke file sementara
            output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
            subclip.write_videofile(output_path, codec='libx264', audio_codec='aac', logger=None)

            with open(output_path, "rb") as f:
                st.download_button(
                    label=f"📥 Download Clip {idx+1}",
                    data=f,
                    file_name=f"clip_{idx+1}.mp4",
                    mime="video/mp4"
                )

    clip.close()
else:
    st.info("Silakan upload video terlebih dahulu.")