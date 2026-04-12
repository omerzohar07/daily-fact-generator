from moviepy import VideoFileClip, AudioFileClip
import random

def merge_fact_video(video_input_path, audio_input_path, output_path="final_short.mp4"):
    """
    Takes a long video and a short audio, cuts a random segment
    from the video, and merges them.
    """
    try:
        # 1. Load the files
        video = VideoFileClip(video_input_path)
        audio = AudioFileClip(audio_input_path)

        # 2. Get durations
        audio_duration = audio.duration
        video_duration = video.duration

        # 3. Safety Check: Ensure the parkour video is long enough
        if video_duration < audio_duration:
            print("Error: The parkour video is shorter than the audio!")
            return

        # 4. Pick a random start time
        # We subtract audio_duration so we don't run out of video at the end
        max_start_time = video_duration - audio_duration - 2  # 2s buffer
        start_time = random.uniform(0, max_start_time)

        # 5. Cut the random segment and set the audio
        # We use subclip(start, end)
        final_clip = video.subclipped(start_time, start_time + audio_duration).with_audio(audio)
        # 6. Write the result
        # 'libx264' is best for social media (TikTok/Reels/Shorts)
        print(f"--- Rendering Video ({audio_duration:.2f}s) starting at {start_time:.2f}s ---")
        final_clip.write_videofile(output_path,
                                   codec="libx264",
                                   audio_codec="aac",
                                   fps=60)

        # 7. Cleanup to free up RAM (important for Data Engineers!)
        video.close()
        audio.close()
        print(f"--- Done! Video saved at: {output_path} ---")

    except Exception as e:
        print(f"An error occurred during video processing: {e}")