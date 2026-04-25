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
            f"Today is {today}. Find one historically verified, yet 'hidden' or suppressed event "
            f"that occurred on this calendar date.\n\n"
            f"OBJECTIVE: Write a 50-60 second YouTube Short script (approx. 140 words).\n\n"
            f"STRUCTURE:\n"
            f"1. THE SHATTERED ANCHOR (0-5s): Start with a known historical fact, then immediately break it. "
            f"Format: '[Well-known person/place] didn't [well-known event]. They [shocking truth].'\n"
            f"2. THE INVESTIGATION (5-20s): Provide the 'Who, Where, and When' clearly. Anchor the viewer's brain. "
            f"Detail: Give 3 fast, concrete pieces of evidence (names, specific numbers, or leaked documents).\n"
            f"3. THE 'WHY IT MATTERS' (20-45s): Connect this event to why the world looks different today. Why was this 'lost'?\n"
            f"4. THE PROFESSOR'S EXIT (45-60s): End with a question that makes the viewer doubt what they learned in school.\n\n"
            f"STRICT RULES:\n"
            f"- TONE: Authoritative, fast-paced, and slightly skeptical.\n"
            f"- STYLE: Use 'The Professor' persona—not a storyteller, but a whistleblower of history.\n"
            f"- CLARITY: No abstract poetry. If there is an object, name the owner.\n"
            f"- NO INTROS: Start with the first word of the hook.\n"
            f"- OUTPUT: Spoken words ONLY.\n"
            f"- LANGUAGE: English."
        )
        return self.model.generate_response(prompt)

class FactValidator(AiInstructor):
    """Specialized in professional fact-checking."""
    def verify(self, fact_text: str):
        prompt = (
            f"You are a Script Doctor and Fact-Checker for a Viral Mystery channel.\n\n"
            f"--- TEXT START ---\n{fact_text}\n--- TEXT END ---\n\n"
            f"TASKS:\n"
            f"1. FACT-CHECK: Verify dates and names. Replace myths with gritty, verifiable truth.\n"
            f"2. DARKEN: Ensure the tone is aggressive and mysterious. Replace 'teacher' phrases with high-stakes transitions.\n"
            f"3. CLEANUP: Strip all stage directions, labels, and parentheses.\n"
            f"4. TITLE GENERATION: Create a high-CTR, 3-5 word title that creates an 'open loop' for the viewer.\n\n"
            f"OUTPUT FORMAT: Return ONLY a valid JSON object with these keys:\n"
            f"{{ \n"
            f"  \"title\": \"The Clickbait Title\",\n"
            f"  \"script\": \"The final spoken narration\"\n"
            f"}}\n\n"
            f"STRICT RULES:\n"
            f"- Output ONLY the JSON.\n"
            f"- No commentary or intro text.\n"
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