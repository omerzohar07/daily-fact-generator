import random
import whisper
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
# Import vfx for cropping
from moviepy.video.fx.Crop import Crop
import requests
import os


TELEGRAM_KEY = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = 5793111830

def send_to_telegram(video_path, caption="New Mystery Video!"):
    token = TELEGRAM_KEY
    chat_id = TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{token}/sendVideo"
    
    with open(video_path, 'rb') as video_file:
        payload = {
            'chat_id': chat_id,
            'caption': caption,
            'supports_streaming': True # Allows users to watch while downloading
        }
        files = {'video': video_file}
        
        print("--- Sending Video to Telegram ---")
        response = requests.post(url, data=payload, files=files)
        
        if response.status_code == 200:
            print("Successfully sent to Telegram!")
        else:
            print(f"Failed to send: {response.text}")


def add_subtitles(video_clip, audio_path):
    print("--- Transcribing Audio for Subtitles ---")
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, word_timestamps=True)
    
    subtitle_clips = []
    
    # Get center of the now-vertical video for positioning
    video_width, video_height = video_clip.size 
    
    for segment in result['segments']:
        for word in segment['words']:
            text = word['word'].upper().strip()
            start = word['start']
            end = word['end']
            duration = end - start
            
            safe_width = int(video_width * 0.9)

            txt_clip = TextClip(
                text=text,
                font="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
                font_size=100,
                color='yellow',
                stroke_color='black',
                stroke_width=3,
                method='caption',         # 'caption' handles wrapping and boundaries better than 'label'
                size=(safe_width, None),  # This forces a horizontal boundary
                text_align='center'            # Centers the text within that boundary
            ).with_start(start).with_duration(duration).with_position(('center', video_height / 2))
            
            subtitle_clips.append(txt_clip)

    return CompositeVideoClip([video_clip] + subtitle_clips)

def merge_fact_video(video_input_path, audio_input_path, output_path="final_vertical_short.mp4"):
    try:
        video = VideoFileClip(video_input_path)
        audio = AudioFileClip(audio_input_path)

        # 1. CALCULATE VERTICAL GEOMETRY
        # Target aspect ratio is 9:16. We scale height to 1920 and crop width to 1080.
        print("--- Reformatting to Vertical (9:16) ---")
        
        # Scale video so the height is 1920
        # 1. CALCULATE VERTICAL GEOMETRY
        print("--- Reformatting to Vertical (9:16) ---")
        
        # Scale video so the height is 1920 (this makes it a very wide 16:9)
        video_scaled = video.resized(height=1920)
        curr_w, curr_h = video_scaled.size
        
        # CORRECT CROP: Don't pass the clip into Crop(), pass it into .apply()
        video_vertical = Crop(
            width=1080, 
            height=1920, 
            x_center=curr_w / 2, 
            y_center=curr_h / 2
        ).apply(video_scaled)
        
        audio_duration = audio.duration
        video_duration = video_vertical.duration

        if video_duration < audio_duration:
            print("Error: The gameplay video is shorter than the audio!")
            return

        max_start_time = video_duration - audio_duration - 2
        start_time = random.uniform(0, max_start_time)

        print(f"--- Slicing Video: {audio_duration:.2f}s starting at {start_time:.2f}s ---")
        base_clip = video_vertical.subclipped(start_time, start_time + audio_duration).with_audio(audio)

        # 2. ADD SUBTITLES TO THE VERTICAL CLIP
        final_video = add_subtitles(base_clip, audio_input_path)

        print("--- Rendering Final Vertical Video ---")
        final_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=60, 
            logger='bar'
        )

        video.close()
        audio.close()
        print(f"--- Done! Vertical project saved at: {output_path} ---")

    except Exception as e:
        print(f"An error occurred during video processing: {e}")