import os
import asyncio
import datetime
import google.generativeai as genai
import edge_tts
from abc import ABC, abstractmethod


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

    def format_script(self, fact: str):
        prompt = (
            f"Rewrite this fact into a script for a 30-second TikTok.\n"
            f"Fact: {fact}\n"
            "STRICT RULES:\n1. Row 1 is a Hook. 2. 8-10 rows total. 3. Max 7 words per row."
        )
        return self.model.generate_response(prompt).split('\n')

# --- 4. Specialized Agents (Inherit from Instructor) ---
class FactGenerator(AiInstructor):
    """Specialized in researching history."""
    def fetch_daily_fact(self):
        today = datetime.datetime.now().strftime("%B %d")
        prompt = f"Today is {today}. Research a shocking daily fact for this date."
        return self.model.generate_response(prompt)

class FactValidator(AiInstructor):
    """Specialized in professional fact-checking."""
    def verify(self, fact_text: str):
        prompt = f"Fact-check this: '{fact_text}'. Return the fact (if validated), else, the correction."
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