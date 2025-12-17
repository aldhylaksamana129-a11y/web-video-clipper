import streamlit as st
from moviepy.editor import VideoFileClip
import tempfile

# Konfigurasi halaman
st.set_page_config(page_title="Web Video Clipper", layout="wide")

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

    st.title("🎥 Web Video Clipper")

    uploaded_file = st.file_uploader("Upload Video", type=["mp4", "mov", "avi", "mkv"])

    if uploaded_file is not None:
        # Simpan file sementara
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_file.read())

        # Dapatkan durasi video
        clip = VideoFileClip(tfile.name)
        duration = clip.duration

        col1, col2 = st.columns(2)

        with col1:
            start_time = st.slider("Waktu Awal (detik)", 0.0, duration, 0.0, step=0.1)
        with col2:
            end_time = st.slider("Waktu Akhir (detik)", 0.0, duration, min(10.0, duration), step=0.1)

        if start_time >= end_time:
            st.error("Waktu akhir harus lebih besar dari waktu awal.")
        else:
            st.success(f"Memotong dari {start_time}s ke {end_time}s")

            # Tombol untuk memotong
            if st.button("✂️ Potong Video"):
                subclip = clip.subclip(start_time, end_time)

                output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                subclip.write_videofile(output_path, codec='libx264', audio_codec='aac', logger=None)

                with open(output_path, "rb") as file:
                    st.download_button(
                        label="📥 Download Video Hasil",
                        data=file,
                        file_name="video_hasil.mp4",
                        mime="video/mp4"
                    )

        # Preview video
        st.video(tfile.name)

        clip.close()
    else:
        st.info("Silakan upload video terlebih dahulu.")