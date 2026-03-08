from ai_companion.modules.image.image_to_text import ImageToText
from ai_companion.modules.image.text_to_image import TextToImage
from ai_companion.modules.speech.text_to_speech import TextToSpeech
from ai_companion.modules.speech.speech_to_text import SpeechToText
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field, EmailStr
from typing import Literal, Optional
from langchain_community.utilities import SQLDatabase
from ai_companion.settings import settings
import os

def get_chat_model(from_subgraph = False, temperature: float = 0.7):
    if from_subgraph:
        return ChatGroq(
        api_key=settings.GROQ_API_KEY1,
        model_name=settings.TEXT_MODEL_NAME_SUBGRAPH,
        temperature=temperature
        )
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name=settings.TEXT_MODEL_NAME,
        temperature=temperature
        )

def get_db():
    db_path = os.path.join(os.path.dirname(__file__), "Chinook.db")
    db = SQLDatabase.from_uri(f"sqlite:///{db_path}", sample_rows_in_table_info=2)
    return db

def get_text_to_speech_module():
    return TextToSpeech()

def get_speech_to_text_module():
    return SpeechToText()

def get_text_to_image_module():
    return TextToImage()

def get_image_to_text_module():
    return ImageToText()

class RouterResponse(BaseModel):
    response_type : Literal['conversation', 'image', 'audio'] = Field(
        description="The response type to give to user. It must be one of : 'conversation', 'image' or 'audio'"
    )

class IntentStructure(BaseModel):
    decision: Literal["Ambiguous", "Unsafe", "Valid"]
    explaination: str
    email: Optional[EmailStr]

class EmailDraft(BaseModel):
    subject: str = Field(description="A catchy, professional subject line")
    body: str = Field(description="The full email body based on SQL data and AVA's personality")

class SQLStructure(BaseModel):
    SQL_query: str
    explaination : str