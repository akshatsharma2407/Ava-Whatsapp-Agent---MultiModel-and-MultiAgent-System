from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=('.env', '../.env'), extra="ignore", env_file_encoding="utf-8")

    GROQ_API_KEY: str
    GROQ_API_KEY1: str
    WHATSAPP_TOKEN: str
    WHATSAPP_PHONE_NUMBER_ID: str
    WHATSAPP_VERIFY_TOKEN: str
    ELEVENLABS_API_KEY: str
    ELEVENLABS_VOICE_ID: str
    HUGGINGFACE_TOKEN: str

    QDRANT_API_KEY: str | None
    QDRANT_URL: str 
    QDRANT_PORT: str = "6333"
    QDRANT_HOST: str | None = None

    TEXT_MODEL_NAME: str = "llama-3.3-70b-versatile"
    TEXT_MODEL_NAME_SUBGRAPH: str = 'openai/gpt-oss-safeguard-20b'
    SMALL_TEXT_MODEL_NAME: str = "llama-3.3-70b-versatile"
    STT_MODEL_NAME: str = "whisper-large-v3-turbo"
    TTS_MODEL_NAME: str = "eleven_flash_v2_5"
    TTI_MODEL_NAME: str = "stabilityai/stable-diffusion-xl-base-1.0"
    ITT_MODEL_NAME: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    gmail_password: str

    TAVILY_API_KEY: str

    MEMORY_TOP_K: int = 3
    ROUTER_MESSAGES_TO_ANALYZE: int = 3
    TOTAL_MESSAGES_SUMMARY_TRIGGER: int = 20
    TOTAL_MESSAGES_AFTER_SUMMARY: int = 5

    SHORT_TERM_MEMORY_DB_PATH: str = "/app/data/memory.db"


settings = Settings()