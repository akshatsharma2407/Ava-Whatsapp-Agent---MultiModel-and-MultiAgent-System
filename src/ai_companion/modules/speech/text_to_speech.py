import os
from typing import Optional
from ai_companion.settings import settings
from elevenlabs import ElevenLabs, Voice, VoiceSettings

class TextToSpeech:
    """A class to handle text-to-speech conversation using ElevanLabs"""

    REQUIRED_ENV_VARS = ["ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID"]

    def __init__(self):
        """Initialize the TextToSpeech class and validate environment variables."""
        self._validate_env_vars()
        self._client: Optional[ElevenLabs] = None

    
    def _validate_env_vars(self):
        """Validate that all required environment variables are set"""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables {', '.join(missing_vars)}")
    
    def get_client(self):
        """Get or create Elevenlabs client instance using singleton pattern (within scope of one object)"""
        if self._client is None:
            self._client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        return self._client
    
    def synthesize(self, text: str):
        """Convert text to speech using ElevenLabs.

        Args:
            text: Text to convert to speech

        Returns:
            bytes: Audio data

        Raises:
            ValueError: If the input text is empty or too long
            TextToSpeechError: If the text-to-speech conversion fails
        """

        if not text.strip():
            raise ValueError("Input text cannot be empty")
        
        if len(text) > 5000:
            raise ValueError("Input text exceeds maximum length of 5000 characters")
        
        try:
            audio_generator = self.get_client().text_to_speech.convert(
                voice_id=settings.ELEVENLABS_VOICE_ID,
                text=text,
                model_id=settings.TTS_MODEL_NAME,
                voice_settings= VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.5
                )
            )

            audio_bytes = b"".join(audio_generator)
            if not audio_bytes:
                raise RuntimeError("Generated audio is empty")
            
            return audio_bytes
        
        except Exception as e:
            raise RuntimeError(f"Text-to-speech conversion Failed: {str(e)}")