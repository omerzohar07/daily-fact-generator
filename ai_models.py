import datetime
from openai import BaseModel, OpenAI
import google.generativeai as genai
import edge_tts
from abc import ABC, abstractmethod
import whisper

# --- 1. Base Model Interface ---
class BaseAIModel(ABC):
    """Abstract interface for any AI Model."""
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        pass

# --- 2. Concrete Gemini Implementation ---
class GeminiModel(BaseAIModel):
    """Implementation of the Gemini API."""
    def __init__(
            self, 
            api_key: str, 
            model_name: str = 'gemini-2.5-flash-lite', 
            system_instruction: str = ""
        ):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction
        )

    def generate_response(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text.strip()

class ChatGPTModel(BaseAIModel):
    """Implementation of the OpenAI ChatGPT API."""
    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-4o-mini",
        system_instruction: str = ""
    ):
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        self.system_instruction = system_instruction

    def generate_response(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": self.system_instruction},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    
# --- 3. The Instructor (Handles logic & Persona) ---
class AiInstructor:
    """Orchestrates generation (Gemini) and validation (ChatGPT)."""
    
    def __init__(self, generator_model: BaseAIModel, validator_model: BaseAIModel):
        self.generator_model = generator_model
        self.validator_model = validator_model

    def get_fact(self):
        generator = FactGenerator(self.generator_model)
        return generator.fetch_daily_fact()

    def validate(self, fact: str):
        validator = FactValidator(self.validator_model)
        return validator.verify(fact)

# --- 4. Specialized Agents (Inherit from Instructor) ---
class FactGenerator():

    def __init__(self, model: BaseAIModel):
        self.model = model
    
    """Specialized in researching history."""
    def fetch_daily_fact(self):
        today = datetime.datetime.now().strftime("%B %d")
        prompt = (
            f"Today is {today}. Find ONE historically verified, high-stakes moment involving a world-famous figure "
            f"(President, A-list icon, founder, etc.).\n\n"

            f"PRIORITY:\n"
            f"- Prefer events tied to this calendar date.\n"
            f"- If none are truly compelling, choose the most dramatic verified moment from history instead.\n\n"

            f"SELECTION RULE:\n"
            f"- The moment MUST include at least one of the following:\n"
            f"  • A high-risk decision\n"
            f"  • A major rejection or failure\n"
            f"  • A point of no return\n"
            f"  • A hidden turning point with real consequences\n"
            f"- If the event is not inherently dramatic, DISCARD it and pick a better one.\n\n"

            f"OBJECTIVE:\n"
            f"Write a 50–60 second high-retention script (~140 words).\n\n"

            f"STRUCTURE:\n"
            f"1. HOOK (0–5s): Start with a 3–6 word curiosity hook that creates an open loop.\n"
            f"   - It must feel like a reveal, not a summary.\n"
            f"   - Avoid generic phrasing like 'is known for' or 'is defined by'.\n\n"

            f"2. THE MOMENT (5–20s): Deliver the core event with sharp, concrete details.\n"
            f"   - Include at least 2–3 specific facts (numbers, locations, exact actions, or quotes).\n\n"

            f"3. THE TURN (20–45s): Show the consequence.\n"
            f"   - What changed because of this moment?\n"
            f"   - Why was this a point of no return?\n\n"

            f"4. MODERN IMPACT (45–55s): Connect it directly to the viewer’s world today.\n"
            f"   - A habit, product, platform, or behavior they recognize.\n\n"

            f"5. FINAL LINE (55–60s): End with a sharp, humanizing reflection + a question.\n\n"

            f"STRICT RULES:\n"
            f"- 100% real, verified history. No myths, no speculation.\n"
            f"- NO conspiracy framing, no 'hidden truth' tone.\n"
            f"- Keep sentences tight and spoken.\n"
            f"- No labels, no stage directions, no brackets.\n"
            f"- Language: English.\n"
        )
        return self.model.generate_response(prompt)

class FactValidator():

    def __init__(self, model: BaseAIModel):
        self.model = model  
        
    """Specialized in professional fact-checking."""
    def verify(self, fact_text: str):
        prompt = (
            "You are a senior Script Editor and Fact-Checker for a viral educational and mysterious Shorts channel.\n\n"

            f"--- SCRIPT START ---\n{fact_text}\n--- SCRIPT END ---\n\n"

            "TASKS:\n"
            "1. FACT-CHECK:\n"
            "- Ensure all names, dates, and claims are accurate.\n"
            "- Remove any exaggeration or vague claims.\n\n"

            "2. HOOK UPGRADE:\n"
            "- Rewrite ONLY the first line if needed.\n"
            "- Make it punchy, curiosity-driven, and impossible to scroll past.\n"
            "- Keep it under 6 words.\n\n"

            "3. TIGHTEN PACING:\n"
            "- Remove filler words.\n"
            "- Replace weak transitions with sharp phrasing.\n"
            "- Make every sentence move the story forward.\n\n"

            "4. INCREASE TENSION:\n"
            "- Emphasize decision, risk, or consequence.\n"
            "- Make the turning point feel irreversible.\n\n"

            "5. TITLE (CRITICAL):\n"
            "- Generate a 3–5 word curiosity title.\n"
            "- Avoid generic words.\n"
            "- Make it highly clickable.\n\n"

            "OUTPUT FORMAT (STRICT JSON ONLY):\n"
            "{\n"
            '  "valid": true,\n'
            '  "title": "3-5 word curiosity title",\n'
            '  "script": "Final 140–160 word narration"\n'
            "}\n\n"

            "RULES:\n"
            "- No text outside JSON.\n"
            "- No markdown.\n"
            "- Keep it natural and fast-paced.\n"
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
class WhisperModel(BaseAIModel):
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