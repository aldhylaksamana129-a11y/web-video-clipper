import streamlit as st
from moviepy.editor import VideoFileClip, AudioFileClip
import tempfile
import os
import cv2
from scenedetect import detect, ContentDetector, open_video
import numpy as np

# Untuk deteksi warna dominan
try:
    from sklearn.cluster import KMeans
except ImportError:
    KMeans = None

# Konfigurasi halaman
st.set_page_config(page_title="Web Video Clipper Pro", layout="wide")

# Simulasi login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "1234":
            st.session_state.logged_in = True
            st.success("Login berhasil!")
            st.rerun()
        else:
            st.error("Username atau password salah")
else:
    st.sidebar.success(f"Logged in as {username}")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("🎥 Web Video Clipper Pro")

    # Upload video
    uploaded_files = st.file_uploader("Upload Video", type=["mp4", "mov", "avi", "mkv"], accept_multiple_files=True)

    if uploaded_files:
        for idx, uploaded_file in enumerate(uploaded_files):
            st.subheader(f"🎬 Video {idx + 1}: {uploaded_file.name}")

            # Simpan file sementara
            tfile = tempfile.NamedTemporaryFile(delete=False)
            tfile.write(uploaded_file.read())
            tfile_path = tfile.name

            # Dapatkan durasi video
            clip = VideoFileClip(tfile_path)
            duration = clip.duration

            # Preview video
            st.video(tfile_path)

            # Pilih metode potong
            method = st.radio("Metode Potong", ["Manual", "Auto (Scene)", "Auto (Face)", "Auto (Color)"])

            if method == "Manual":
                col1, col2 = st.columns(2)
                with col1:
                    start_time = st.slider("Waktu Awal (detik)", 0.0, duration, 0.0, step=0.1)
                with col2:
                    end_time = st.slider("Waktu Akhir (detik)", 0.0, duration, min(10.0, duration), step=0.1)

                if start_time >= end_time:
                    st.error("Waktu akhir harus lebih besar dari waktu awal.")
                else:
                    st.success(f"Memotong dari {start_time}s ke {end_time}s")

            else:
                # Auto clip detection
                with st.spinner("Mendeteksi scene..."):
                    clips = []
                    if method == "Auto (Scene)":
                        try:
                            video = open_video(tfile_path)
                            scenes = detect(video, ContentDetector(threshold=30))
                            for scene in scenes:
                                start = scene[0].get_seconds()
                                end = scene[1].get_seconds()
                                clips.append((start, end))
                        except Exception as e:
                            st.error(f"Error: {e}")
                    elif method == "Auto (Face)":
                        cap = cv2.VideoCapture(tfile_path)
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                        for i in range(0, total_frames, int(fps)):
                            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                            ret, frame = cap.read()
                            if ret:
                                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                                if len(faces) > 0:
                                    start = i / fps
                                    end = start + 2
                                    clips.append((start, end))
                        cap.release()
                    elif method == "Auto (Color)" and KMeans:
                        cap = cv2.VideoCapture(tfile_path)
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                        for i in range(0, total_frames, int(fps)):
                            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                            ret, frame = cap.read()
                            if ret:
                                data = frame.reshape((-1, 3))
                                kmeans = KMeans(n_clusters=1)
                                kmeans.fit(data)
                                dominant_color = kmeans.cluster_centers_[0]
                                if dominant_color.mean() > 200:
                                    start = i / fps
                                    end = start + 1
                                    clips.append((start, end))
                        cap.release()

                    if clips:
                        # Pilih scene pertama
                        start_time, end_time = clips[0]
                        st.success(f"Auto-deteksi scene: {start_time:.2f}s - {end_time:.2f}s")
                    else:
                        st.warning("Tidak ada scene yang terdeteksi.")

            # Pilih format dan filter
            col3, col4 = st.columns(2)
            with col3:
                format_export = st.selectbox("Format Export", ["MP4", "GIF", "MP3"], key=f"format_{idx}")
            with col4:
                filter_preset = st.selectbox("Filter", ["None", "Slow Motion", "Speed Up", "Grayscale", "Reverse"], key=f"filter_{idx}")

            # Tombol potong
            if st.button(f"✂️ Potong Video {idx + 1}", key=f"btn_{idx}"):
                subclip = clip.subclip(start_time, end_time)

                # Apply filter
                if filter_preset == "Slow Motion":
                    subclip = subclip.speedx(0.5)
                elif filter_preset == "Speed Up":
                    subclip = subclip.speedx(2)
                elif filter_preset == "Grayscale":
                    subclip = subclip.fx(lambda c: c.fl_image(lambda img: cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)))
                elif filter_preset == "Reverse":
                    subclip = subclip.fx(lambda c: c.fl_time(lambda t: c.duration - t))

                # Ekspor
                if format_export == "MP4":
                    output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                    subclip.write_videofile(output_path, codec='libx264', audio_codec='aac', logger=None)
                    mime_type = "video/mp4"
                elif format_export == "GIF":
                    output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.gif').name
                    subclip.write_gif(output_path)
                    mime_type = "image/gif"
                elif format_export == "MP3":
                    audio = subclip.audio
                    output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                    audio.write_audiofile(output_path)
                    mime_type = "audio/mp3"

                with open(output_path, "rb") as file:
                    st.download_button(
                        label=f"📥 Download {format_export}",
                        data=file,
                        file_name=f"video_{idx + 1}_hasil.{format_export.lower()}",
                        mime=mime_type,
                        key=f"download_{idx}"
                    )

            st.divider()

    else:
        st.info("Silakan upload video terlebih dahulu.")
