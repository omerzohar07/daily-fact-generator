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
            f"Today is {today}. Find one historically verified, surprising, and high-impact fact "
            f"involving a world-famous figure (e.g., a President, A-list icon, or Tech Giant) "
            f"that occurred or was revealed on this calendar date.\n\n"
            
            f"OBJECTIVE: Write a 50-60 second high-retention script (approx. 140 words).\n\n"
            
            f"STRUCTURE:\n"
            f"1. THE HOOK (0-5s): Start with a surprising contrast to their public image. "
            f"Format: '[Famous Person] is defined by [Known Achievement], but their real turning point happened today. It wasn't [Common Myth]; it was [Surprising Reality].'\n"
            f"2. THE ARCHIVE (5-20s): Provide the 'Hard Data.' Use concrete details: specific addresses, exact numbers, or documented quotes. "
            f"Give 3 rapid-fire facts that prove this event changed the course of their life.\n"
            f"3. THE DOMINO EFFECT (20-45s): Explain the 'Why it matters.' How did this single moment create a ripple effect "
            f"that influences the world the viewer lives in right now? Connect the past to a modern-day habit or product.\n"
            f"4. THE FINAL THOUGHT (45-60s): Deliver a closing line that reframes the icon as a human being rather than a statue. "
            f"End with a question that makes the viewer wonder about their own untapped potential.\n\n"
            
            f"STRICT RULES:\n"
            f"- PERSONA: 'The Archivist'—intelligent, sharp, and slightly witty. No paranoia, only fascinating insight.\n"
            f"- VERACITY: 100% real history. No legends or 'maybe' stories.\n"
            f"- HOOK FOCUS: The first 3 words must be 'scroll-stopping.' Use high-momentum language (e.g., 'The contract signed,' 'The secret audition.').\n"
            f"- NO INTROS: Start immediately. No 'Hey everyone' or 'Welcome back.'\n"
            f"- OUTPUT: Spoken words ONLY. No stage directions or brackets.\n"
            f"- LANGUAGE: English."
        )
        return self.model.generate_response(prompt)

class FactValidator(AiInstructor):
    """Specialized in professional fact-checking."""
    def verify(self, fact_text: str):
        prompt = (
            f"You are a Script Editor and Fact-Checker for a premium Educational Entertainment channel.\n\n"
            f"--- TEXT START ---\n{fact_text}\n--- TEXT END ---\n\n"
            
            f"TASKS:\n"
            f"1. FACT-CHECK: Ensure names, dates, and locations are 100% accurate. Remove any 'conspiracy' or 'cover-up' language.\n"
            f"2. ENERGIZE: Make the tone punchy and sophisticated. Replace boring transitions with high-momentum 'power phrases.'\n"
            f"3. CLEANUP: Ensure there are zero labels, stage directions, or parenthetical notes.\n"
            f"4. TITLE GENERATION: Create a high-CTR, 3-5 word title that uses the 'Gap Theory' (creates a curiosity gap).\n\n"
            
            f"OUTPUT FORMAT: Return ONLY a valid JSON object with these keys:\n"
            f"{{\n"
            f"  \"title\": \"The Famous Figure's Secret\",\n"
            f"  \"script\": \"The final spoken narration\"\n"
            f"}}\n\n"
            
            f"STRICT RULES:\n"
            f"- Output ONLY the JSON.\n"
            f"- No commentary.\n"
            f"- Script length: 140-160 words."
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
        # Load the model into memory once during initialization
        self.model = whisper.load_model(model_size)

    def generate_response(self, audio_path: str) -> dict:
        """
        Transcribes audio. Note: Returns a dict (result) 
        rather than a string to keep the word timestamps.
        """
        result = self.model.transcribe(audio_path, word_timestamps=True)
        return result