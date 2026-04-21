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
            f"Today is {today}. Find a shocking, bizarre, or 'lost' historical event "
            f"that happened on this exact date.\n\n"
            f"WRITING STYLE: Use a 'Pattern Interrupt' hook. Do not summarize history; "
            f"challenge the listener's reality immediately.\n"
            f"Example: 'They want you to believe Napoleon died of natural causes, but the truth is buried in a ghost town.'\n\n"
            f"STRUCTURE:\n"
            f"1. THE HOOK: Start with a jarring contradiction or a morbid impossibility. No 'On this day' intros.\n"
            f"2. THE MEAT: 4-5 fast-paced, eerie details. Use sensory words (blood, shadows, silence, steel).\n"
            f"3. THE TWIST: A final detail that leaves a 'chilling void' or a lingering ghost story.\n"
            f"4. PACING: Use short, punchy sentences. 140-160 words total.\n\n"
            f"STRICT RULES:\n"
            f"- Output ONLY the spoken words.\n"
            f"- Tone: Dark Mystery / Psychological Thriller.\n"
            f"- Avoid 'teacher' language like 'In conclusion' or 'It is important to note'.\n"
            f"- Language: English."
        )
        return self.model.generate_response(prompt)

class FactValidator(AiInstructor):
    """Specialized in professional fact-checking."""
    def verify(self, fact_text: str):
        prompt = (
            f"You are a Script Doctor for a Viral Mystery channel. "
            f"Fact-check and 'Darken' the following text:\n\n"
            f"--- TEXT START ---\n{fact_text}\n--- TEXT END ---\n\n"
            f"TASKS:\n"
            f"1. FACT-CHECK: Verify all dates/names. If a detail is a common myth, replace it with the gritty, verifiable truth.\n"
            f"2. REMOVE THE 'TEACHER': Delete phrases like 'the truth is more chilling' or 'that claim is a myth.' "
            f"Instead, use aggressive transitions like 'The records are a lie' or 'The reality is much darker.'\n"
            f"3. CLEANUP: Strip all labels (HOOK:, VO:), stage directions, and parentheses.\n"
            f"4. FLOW: Ensure the script is one seamless block of text for a deep-voiced, rhythmic narrator.\n"
            f"5. OUTPUT ONLY THE FINAL SPOKEN SCRIPT. No intro/outro commentary."
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