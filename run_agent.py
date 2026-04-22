import asyncio
import os
import json
from dotenv import load_dotenv
import re
import logging

from ai_models import GeminiModel, AiInstructor, Voice
from utils import merge_fact_video, send_to_telegram, wait_for_approval
from config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
IS_LOCAL_DEBUGGING = os.getenv("LOCAL_DEBUGGING") == "true"
NEW_REEL_FILE_NAME = "final_vertical_short.mp4"

# --- Main Execution ---
async def main():
    if not API_KEY:
        logger.error("No API Key found. Exiting...")
        return
    
    if IS_LOCAL_DEBUGGING:
        logger.info("Mode: Local Debugging, Loading from fact.txt")
        if os.path.exists('fact.txt'):
            with open('fact.txt', 'r', encoding='utf-8') as f:
                validated_fact = f.read()
        else:
            logger.error("fact.txt not found!")
            return
    
    else:
        sys_msg = "You are a Viral Content Specialist. Style: Mystery/Thriller."
        llm = GeminiModel(api_key=API_KEY, system_instruction=sys_msg)
        instructor = AiInstructor(llm)

        approved = False
        while not approved:
            logger.info("--- Phase: Generating New Fact ---")
            try:
                raw_fact = instructor.get_fact()
                validated_response = instructor.validate(raw_fact)
                
                # Clean markdown code blocks if the AI included them
                cleaned_json = re.sub(r"```json\n?|```", "", validated_response).strip()
                data = json.loads(cleaned_json)

                validated_fact = data.get("script", "")
                title = data.get("title", "Unknown Mystery")

                if not validated_fact:
                    logger.warning("AI returned empty script. Retrying...")
                    continue
                
                logger.info(f"Fact Generated: {title}. Sending for approval...")
                send_to_telegram(daily_fact=f"📝 *PROPOSED SCRIPT:*\n\n{validated_fact}")

                approved = wait_for_approval()
                
                if not approved:
                    logger.warning("Fact rejected. Generating a new one...")
                else:
                    logger.info("Fact approved! Moving to production.")
                    break
            
            except json.JSONDecodeError:
                logger.error("Failed to parse AI JSON. Raw output: %s", validated_response)
                continue
            except Exception as e:
                logger.error(f"Error during generation loop: {e}")
                await asyncio.sleep(5) # Brief pause before retry

    
    logger.info("--- Phase: Voiceover Generation ---")
    audio_file = await Voice().generate_audio(validated_fact)

    logger.info("--- Phase: Video Merging (MoviePy) ---")
    merge_fact_video(video_input_path="minecraft-parkour-gameplay-vertical.mp4", 
                    audio_input_path=audio_file,
                    music_input_path="bm.mp3",
                    output_path=NEW_REEL_FILE_NAME
                    )
                     
    logger.info("--- Phase: Final Video Approval ---")
    send_to_telegram(video_path=NEW_REEL_FILE_NAME)
    
    is_approved = wait_for_approval()
    if is_approved:
        logger.info(f"✅ Approved! Ready for YouTube: {title}")
        from youtube_uploader import upload_video
        upload_video(NEW_REEL_FILE_NAME, title=title)
        


if __name__ == "__main__":
    asyncio.run(main())