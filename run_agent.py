import asyncio
import os
# Import your custom logic from the other file
from ai_models import GeminiModel, AiInstructor, Voice, FactValidator
from utils import merge_fact_video

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# --- Main Execution ---
async def main():
    if not API_KEY:
        print("No API Key found. Returning...")
        return
    
    sys_msg = "You are a Viral Content Specialist. Style: Mystery/Thriller."
    
    # Initialize components
    llm = GeminiModel(api_key=API_KEY, system5_instruction=sys_msg)
    instructor = AiInstructor(llm)
    voice_engine = Voice()

    # 1. Generate & Validate
    print("--- Generating Fact ---")
    # raw_fact = instructor.get_fact()
    # validated_fact = instructor.validate(raw_fact)
    # print(f"Fact: {validated_fact}")
    
    # with open('fact.txt', 'w', encoding='utf-8') as f:
    #     f.write(validated_fact)

    with open('fact.txt', 'r', encoding='utf-8') as f:
        validated_fact = f.read()

    # 2. Generate Audio
    print("--- Generating Voiceover ---")
    audio_file = await voice_engine.generate_audio(validated_fact)

    # 3. Merge Video (Ensure the MP4 file exists in your directory!)
    merge_fact_video(video_input_path="minecraft-parkour-gameplay.mp4", audio_input_path=audio_file)

if __name__ == "__main__":
    asyncio.run(main())