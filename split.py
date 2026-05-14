import streamlit as st
import os
import zipfile
import tempfile
import shutil
import time
from moviepy import VideoFileClip

# 1. Page Config - Forces Light Mode aesthetic
st.set_page_config(page_title="Video Splitter", page_icon="✂️", layout="centered")

# 2. Forced CSS for flat white branding and visible text
st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    h1, h2, h3, p, span, label, .stMarkdown { 
        color: #1f2937 !important; 
        text-align: center; 
    }
    h1 { font-weight: 800 !important; font-size: 3.5rem !important; margin-top: 2rem !important; }
    .subtitle { font-size: 1.2rem !important; color: #4b5563 !important; margin-bottom: 3rem !important; }
    .stButton>button { 
        background-color: #3b82f6 !important; color: white !important; 
        border-radius: 8px !important; width: 220px !important; height: 3em !important;
        margin: 0 auto !important; display: block !important; font-weight: bold !important;
    }
    .feature-item p, .feature-header { text-align: left !important; color: #1f2937 !important; }
    .feature-header { border-bottom: 3px solid #3b82f6; display: inline-block; margin-bottom: 10px; font-weight: bold; }
    .stProgress > div > div > div > div { background-color: #3b82f6 !important; }
    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

def split_video(uploaded_file):
    # Use mkdtemp for manual cleanup control on Windows
    tmp_dir = tempfile.mkdtemp()
    try:
        temp_input_path = os.path.join(tmp_dir, uploaded_file.name)
        with open(temp_input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        output_dir = os.path.join(tmp_dir, "segments")
        os.makedirs(output_dir)

        segment_length = 300 
        output_paths = []

        clip = VideoFileClip(temp_input_path)
        duration = clip.duration
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        start_time, index = 0, 1
        total_segments = int(duration // segment_length) + (1 if duration % segment_length > 0 else 0)

        while start_time < duration:
            status_text.markdown(f"**Processing segment {index} of {total_segments}...**")
            end_time = min(start_time + segment_length, duration)
            
            # Version compatibility for subclip
            sub = clip.subclipped(start_time, end_time) if hasattr(clip, "subclipped") else clip.subclip(start_time, end_time)
            
            out_path = os.path.join(output_dir, f"part_{index}_{uploaded_file.name}")
            
            # --- FIX: Compatibility for MoviePy 1.x and 2.x ---
            try:
                # Try MoviePy 1.x style
                sub.write_videofile(out_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)
            except TypeError:
                # Fallback for MoviePy 2.x style (verbose/logger removed)
                sub.write_videofile(out_path, codec="libx264", audio_codec="aac", logger=None)
            
            output_paths.append(out_path)
            progress_bar.progress(index / total_segments)
            start_time += segment_length
            index += 1
        
        # Aggressive file release to prevent PermissionError
        clip.close()
        if hasattr(clip, 'reader') and clip.reader:
            clip.reader.close()
        if clip.audio and hasattr(clip.audio, 'reader') and clip.audio.reader:
            clip.audio.reader.close()
        del clip 
        
        zip_path = os.path.join(tempfile.gettempdir(), f"split_{os.urandom(4).hex()}.zip")
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in output_paths:
                zipf.write(file, os.path.basename(file))
        
        progress_bar.empty()
        status_text.empty()
        return zip_path

    except Exception as e:
        st.error(f"Error: {e}")
        return None
    finally:
        # Give Windows a moment to release handles before deletion
        time.sleep(0.3)
        shutil.rmtree(tmp_dir, ignore_errors=True)

# --- UI CONTENT ---
st.markdown("<h1>5 Minute Clips</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Turn long recordings into bite-sized 5-minute clips instantly.</p>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload", type=['mp4', 'mov', 'mkv', 'avi'], label_visibility="collapsed")

if uploaded_file:
    if st.button("Split Video"):
        result_zip = split_video(uploaded_file)
        if result_zip:
            with open(result_zip, "rb") as f:
                st.download_button("Download ZIP Archive", f, file_name="video_segments.zip")
            if os.path.exists(result_zip):
                os.remove(result_zip)

st.markdown("<br><br><hr><br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="feature-item"><p class="feature-header">Any format</p><p>Supporting almost every video format. If you can play it, we can split it.</p></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="feature-item"><p class="feature-header">Easy splitting</p><p>No complicated timelines. Upload your file and get your segments in one click.</p></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="feature-item"><p class="feature-header">Security guaranteed</p><p>Privacy is key. Your files are processed and then deleted automatically.</p></div>', unsafe_allow_html=True)