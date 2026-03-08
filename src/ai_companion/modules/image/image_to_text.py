import base64
import os
from typing import Optional, Union
from ai_companion.settings import settings
from groq import Groq

class ImageToText:
    """A class to handle image-to-text conversion using Groq vision capabilites"""
    REQUIRED_ENV_VARS = ['GROQ_API_KEY1']

    def __init__(self):
        """Initialize the ImagetoText class and validate environment variables"""
        self._validate_env_vars()
        self._client: Optional[Groq] = None
    
    def _validate_env_vars(self):
        """Validate that all required environment variables are set"""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    def get_client(self):
        """Got or create Groq client instance using singleton pattern in scope of one object"""
        if self._client is None:
            self._client = Groq(api_key=settings.GROQ_API_KEY)
        return self._client
    
    def analyze_image(self, image_data: Union[str, bytes], prompt: str = ""):
        """Analyze an image using Groq's vision capabilites"""
        try:
            if isinstance(image_data, str):
                if not os.path.exists(image_data):
                    raise ValueError(f"Image file not found: {image_data}")
                with open(image_data, "rb") as f:
                    image_bytes = f.read()
            else:
                image_bytes = image_data
            
            if not image_bytes:
                raise ValueError('Image data cannot be empty')
            
            base64_image  = base64.b64encode(image_bytes).decode('utf-8')

            if not prompt:
                prompt = "please describe what you see in this image in detail, never say that you can't see image, you have capability of seeing image"
            
            messages = [
                {
                    "role" : "user",
                    "content" : [
                        {
                            "type" : "text",
                            "text" : prompt
                        },
                        {
                            "type" : "image_url",
                            "image_url" : {"url" : f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ]

            response = self.get_client().chat.completions.create(
                model=settings.ITT_MODEL_NAME,
                messages=messages,
                max_completion_tokens=1000
            )

            if not response.choices:
                raise RuntimeError(f"No response received from vision model (image to text model)")
            
            description = response.choices[0].message.content
            
            return description
        
        except Exception as e:
            raise RuntimeError(f"Failed to analyse image: {str(e)}")