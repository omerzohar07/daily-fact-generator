import datetime
import google.generativeai as genai
import edge_tts
from abc import ABC, abstractmethod
import whisper

# --- 1. Base Model Interface ---
class BaseModel(ABC):
    """Abstract interface for any AI Model."""
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        pass

# --- 2. Concrete Gemini Implementation ---
class GeminiModel(BaseModel):
    """Implementation of the Gemini API."""
    def __init__(self, api_key: str, model_name: str = 'gemini-2.5-flash-lite', system_instruction: str = ""):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction
        )

    def generate_response(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text.strip()

# --- 3. The Instructor (Handles logic & Persona) ---
class AiInstructor:
    """Orchestrates the creation and validation process."""
    def __init__(self, model: BaseModel):
        self.model = model

    def get_fact(self):
        generator = FactGenerator(self.model)
        return generator.fetch_daily_fact()

    def validate(self, fact: str):
        validator = FactValidator(self.model)
        return validator.verify(fact)


# --- 4. Specialized Agents (Inherit from Instructor) ---
class FactGenerator(AiInstructor):
    """Specialized in researching history."""
    def fetch_daily_fact(self):
        today = datetime.datetime.now().strftime("%B %d")
        prompt = (
            f"Today is {today}. Find a shocking or bizarre historical event "
            f"that happened on this exact date.\n\n"
            f"Structure the response for a 60-second voiceover:\n"
            f"1. THE HOOK: A gripping opening sentence.\n"
            f"2. THE MEAT: 4-5 escalating, eerie details.\n"
            f"3. THE TWIST: A 'sounds fake but is true' detail.\n"
            f"4. LENGTH: 150-180 words.\n\n"
            f"STRICT RULES:\n"
            f"- Output ONLY the spoken words.\n"
            f"- NO stage directions like '(Camera zooms)' or '(Images flash)'.\n"
            f"- NO scene descriptions or on-screen text labels.\n"
            f"- NO bolding or special formatting.\n"
            f"- Tone: Mystery/Thriller. Language: English."
        )
        return self.model.generate_response(prompt)

class FactValidator(AiInstructor):
    """Specialized in professional fact-checking."""
    def verify(self, fact_text: str):
        prompt = (
            f"You are a professional Investigative Journalist and Script Editor. "
            f"Fact-check and clean the following text:\n\n"
            f"--- TEXT START ---\n{fact_text}\n--- TEXT END ---\n\n"
            f"TASKS:\n"
            f"1. Verify all facts/dates. If it's a myth, replace it with the truth.\n"
            f"2. REMOVE all stage directions, camera cues, and descriptions in parentheses ( ).\n"
            f"3. REMOVE all labels like 'VOICEOVER:' or 'HOOK:'.\n"
            f"4. Ensure the text is one continuous, natural narration for a deep-voiced speaker.\n"
            f"5. OUTPUT ONLY THE FINAL SPOKEN SCRIPT. Nothing else."
        )
        return self.model.generate_response(prompt)
    
# --- 5. Voice & Video Services ---
class Voice:
    """Handles deep voice generation."""
    def __init__(self, voice="en-US-ChristopherNeural"):
        self.voice = voice

    async def generate_audio(self, text, output_filename="fact_audio.mp3"):
        communicate = edge_tts.Communicate(text, self.voice, pitch="-10Hz", rate="+3%")
        await communicate.save(output_filename)
        return output_filename
    

# --- 6. Concrete Whisper Implementation ---
class WhisperModel(BaseModel):
    """Implementation of OpenAI's Whisper for transcription."""
    def __init__(self, model_size: str = "base"):
        print(f"--- Loading Whisper {model_size} Model (Once) ---")
        # Load the model into memory once during initialization
        self.model = whisper.load_model(model_size)

    def generate_response(self, audio_path: str) -> dict:
        """
        Transcribes audio. Note: Returns a dict (result) 
        rather than a string to keep the word timestamps.
        """
        result = self.model.transcribe(audio_path, word_timestamps=True)
        return result