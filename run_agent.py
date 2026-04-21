import asyncio
import os
from dotenv import load_dotenv
# Import your custom logic from the other file
from ai_models import GeminiModel, AiInstructor, Voice
from utils import merge_fact_video, send_to_telegram, wait_for_approval

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
IS_LOCAL_DEBUGGING = os.getenv("LOCAL_DEBUGGING") == "true"
NEW_REEL_FILE_NAME = "final_vertical_short.mp4"

# --- Main Execution ---
async def main():
    if not API_KEY:
        print("No API Key found. Returning...")
        return
    
    if IS_LOCAL_DEBUGGING:
        print("--- Loading Fact from Local File ---")
        if os.path.exists('fact.txt'):
            with open('fact.txt', 'r', encoding='utf-8') as f:
                validated_fact = f.read()
        else:
            print("Error: fact.txt not found!")
            return
    
    else:
        sys_msg = "You are a Viral Content Specialist. Style: Mystery/Thriller."
    
        # Initialize components
        llm = GeminiModel(api_key=API_KEY, system_instruction=sys_msg)
        instructor = AiInstructor(llm)

        approved = False

        while not approved:
            print("--- Generating Fact ---")
            raw_fact = instructor.get_fact()
            validated_fact = instructor.validate(raw_fact)
            
            send_to_telegram(daily_fact=validated_fact)
    
            approved = wait_for_approval()
            
            if not approved:
                print("Fact rejected/deleted. Generating a new one...")

            else:
                print("Fact approved! Proceeding to video generation...")
                break

    print(f"Fact: {validated_fact}")
    
    # 2. Generate Audio.
    print("--- Generating Voiceover ---")
    audio_file = await Voice().generate_audio(validated_fact)

    # 3. Merge Video.
    merge_fact_video(video_input_path="minecraft-parkour-gameplay-vertical.mp4", 
                    audio_input_path=audio_file,
                    music_input_path="bm.mp3",
                    output_path=NEW_REEL_FILE_NAME
                    )
                     

    send_to_telegram(video_path=NEW_REEL_FILE_NAME)
    
    is_approved = wait_for_approval()
    if is_approved:
        print("✅ Approved! Uploading to YouTube...")
        # from youtube_uploader import upload_video
        # upload_video(NEW_REEL_FILE_NAME, title="Daily Shocking Fact!")
        


if __name__ == "__main__":
    asyncio.run(main())