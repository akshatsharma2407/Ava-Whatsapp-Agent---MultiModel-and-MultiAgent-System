import io
import os
from typing import Optional
from huggingface_hub import InferenceClient
from PIL import Image
from ai_companion.core.prompts import IMAGE_SCENARIO_PROMPT
from ai_companion.settings import settings
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

class ScenarioPrompt(BaseModel):
    narrative: str = Field(..., description="The AI's narrative response to the question")
    image_prompt: str = Field(..., description="The visual prompt to generate an image representing the scene")

class EnhancedPrompt(BaseModel):
    content: str = Field(..., description="The enhanced text prompt to generate an image")

class TextToImage:
    """A class to handle text-to-image generation using Hugging Fase Inference API"""

    REQUIRED_ENV_VARS = ["GROQ_API_KEY", "HUGGINGFACE_TOKEN"]

    def __init__(self):
        """Initialize and validate environment variables."""
        self._validate_env_vars()
        self._hf_client : Optional[InferenceClient] = None

    def _validate_env_vars(self):
        """Validate that all required environment variables are set."""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    def get_hfclient(self):
        """Get or create Huggingface Client instance using singleton pattern within scope of one object"""
        if self._hf_client is None:
            self._hf_client = InferenceClient(token=settings.HUGGINGFACE_TOKEN)
        return self._hf_client
    
    def generate_image(self, prompt: str, output_path: str = ""):
        """Generate an image from a prompt using FLUX.1-dev via Hugging Face"""
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        try:
            image: Image.Image =self.get_hfclient().text_to_image(
                prompt=prompt,
                model=settings.TTI_MODEL_NAME,
                guidance_scale=3.5,
                num_inference_steps=28,
                width=1024,
                height=1024
            )

            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            image_data = img_byte_arr.getvalue()

            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                image.save(output_path)
            
            return image_data
        
        except Exception as e:
            raise RuntimeError(f"failed to generate Image: {str(e)}")
    
    def create_scenario(self, chat_history: list = None):
        try:
            formatted_history =  "\n".join([f"{msg.type.title()}: {msg.content}" for msg in chat_history[-5:]])

            llm = ChatGroq(
                model=settings.TEXT_MODEL_NAME,
                api_key=settings.GROQ_API_KEY,
                temperature=0.4,
                max_retries=2,
            )

            structured_llm = llm.with_structured_output(ScenarioPrompt)

            chain = PromptTemplate(input_variables=["chat_history"], template=IMAGE_SCENARIO_PROMPT) | structured_llm

            scneraio = chain.invoke({"chat_history" : formatted_history})

            return scneraio
        
        except Exception as e:
            raise RuntimeError(f"Failed to create scenario: {str(e)}")