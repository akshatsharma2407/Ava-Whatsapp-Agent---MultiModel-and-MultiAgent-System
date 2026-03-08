import os
import tempfile
from typing import Optional
from ai_companion.settings import settings
from groq import Groq

class SpeechToText:
    """A class to handle speech to text conversation using Groq's model"""

    REQUIRED_ENV_VARS = ["GROQ_API_KEY"]

    def __init__(self):
        """Initialize the SpeechToText class and validate environment variables"""
        self._validate_env_vars()
        self._client: Optional[Groq] = None
    
    def _validate_env_vars(self):
        """Validate that all required environment variables are set"""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing Required envinonment variables: {', '.join(missing_vars)}")
        
    def get_client(self):
        """get or create a groq Client using singleton pattern (within object scope)"""
        if self._client is None:
            self._client = Groq(api_key=settings.GROQ_API_KEY)
        return self._client
    
    def transcribe(self, audio_data: bytes):
        """
        convert speech to text using groq wisper model

        Args:
            audio_data: binary audio data
        
        Returns:
            str: Transcribed text
        
        Raises:
            ValueError: If the audio file is empty or invalid
            RuntimeError: if the transcription fails
        """

        if not audio_data:
            raise ValueError("Audio data cannot be empty")
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                with open(temp_file_path, "rb") as audio_file:
                    transcription = self.get_client().audio.transcriptions.create(
                        file=audio_file,
                        model="whisper-large-v3-turbo",
                        temperature=0,
                        response_format='text'
                    )
                
                if not transcription:
                    raise RuntimeError("Transcription result is empty")
                
                return transcription
            
            finally:
                os.unlink(temp_file_path)
        
        except Exception as e:
            raise RuntimeError(f"Speech-to-text conversion failed: {str(e)}")