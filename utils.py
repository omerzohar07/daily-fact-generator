import random
import whisper
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, CompositeAudioClip
# Import vfx for cropping
from moviepy.video.fx.Crop import Crop
import requests
import os
import json
import time
from retry import retry

TELEGRAM_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
IS_LOCAL_DEBUGGING = os.getenv("LOCAL_DEBUGGING") == "true"
last_update_id = -1

@retry(tries=3, delay=30, backoff=1)
def send_to_telegram(daily_fact=None, video_path=None, caption="New Mystery Video!"):
    token = TELEGRAM_KEY
    chat_id = TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{token}/sendVideo"
    
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Approve", "callback_data": "true"},
            {"text": "❌ Delete", "callback_data": "false"}
        ]]
    }
    reply_markup = json.dumps(keyboard)
    
    if daily_fact and not video_path:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': f"📜 *FACT:*\n\n{daily_fact}",
            'parse_mode': 'Markdown',
            'reply_markup': reply_markup
        }
        response = requests.post(url, data=payload)
    
    elif video_path:
        url = f"https://api.telegram.org/bot{token}/sendVideo"
        with open(video_path, 'rb') as video_file:
            payload = {
                'chat_id': chat_id,
                'caption': f"🎬 *VIDEO*\n\n{caption}",
                'supports_streaming': True,
                'reply_markup': reply_markup
            }
            
            files = {'video': video_file}
            response = requests.post(url, data=payload, files=files)   
        
    if response.status_code == 200:
        print("Successfully sent to Telegram!")
    else:
        print(f"Failed to send: {response.text}")


def wait_for_approval():
    print("Waiting for Telegram approval...")
    global last_update_id
    
    while True:
        # Check Telegram for new button clicks (callback_queries)
        url = f"https://api.telegram.org/bot{TELEGRAM_KEY}/getUpdates"
        params = {"offset": last_update_id + 1, "timeout": 30}
        updates = requests.get(url, params=params).json()

        for update in updates.get("result", []):
            last_update_id = update["update_id"]
            
            if "callback_query" in update:
                return update["callback_query"]["data"] == 'true'
        
        time.sleep(2) 

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

            txt_clip = TextClip(
                text=text,
                font="/usr/share/fonts/truetype/montserrat/Montserrat-Bold.ttf", 
                font_size=100,
                color='yellow',
                stroke_color='black',
                stroke_width=2,
                method='caption',    
                size=(int(video_width * 0.75), 200),
                text_align='center'
            ).with_start(start).with_duration(duration).with_position(('center', 'center'))
            
            subtitle_clips.append(txt_clip)

    return CompositeVideoClip([video_clip] + subtitle_clips)

def merge_fact_video(video_input_path, audio_input_path, music_input_path, output_path):
    try:
        video = VideoFileClip(video_input_path)
        voiceover = AudioFileClip(audio_input_path)
        
        # The clip length will be the audio length OR 62s, whichever is longer.
        target_duration = max(62, voiceover.duration)

        # If in local mode, we force a 5-second limit
        if IS_LOCAL_DEBUGGING:
            print("--- Local Mode: Capping video to 5 seconds ---")
            target_duration = 5

        # Load and prepare background music
        bg_music = (AudioFileClip(music_input_path)
                    .with_volume_scaled(0.1)
                    .subclipped(0, target_duration)
        )

        combined_audio = CompositeAudioClip([
            voiceover, bg_music
        ])
        
        print("--- Reformatting to Vertical (9:16) ---")
        # Scale video so the height is 1920 (this makes it a very wide 16:9)
        video_scaled = video.resized(height=1920)
        curr_w, curr_h = video_scaled.size
        
        video_vertical = Crop(
            width=1080, 
            height=1920, 
            x_center=curr_w / 2, 
            y_center=curr_h / 2
        ).apply(video_scaled)
        
        
        video_duration = video_vertical.duration

        if video_duration < target_duration:
            print("Error: The gameplay video is shorter than the audio!")
            return

        max_start_time = video_duration - target_duration - 2
        start_time = random.uniform(0, max_start_time)

        print(f"--- Slicing Video: {target_duration:.2f}s starting at {start_time:.2f}s ---")
        base_clip = video_vertical.subclipped(start_time, start_time + target_duration).with_audio(combined_audio)

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
        voiceover.close()
        bg_music.close()
        combined_audio.close()
        print(f"--- Done! Vertical project saved at: {output_path} ---")

    except Exception as e:
        print(f"An error occurred during video processing: {e}")