from langgraph.graph import MessagesState
from pydantic import EmailStr

class AICompanionState(MessagesState):
    summary: str
    workflow: str
    audio_buffer: bytes
    image_path: str
    memory_context: str

class SQLWorkflowState(MessagesState):
    generated_sql: str 
    reason_behind_generated_sql: str
    feedback: str 
    extra_info: str
    retry_count: int
    result: str
    intent: str
    reason_for_intent: str
    email: EmailStr
    email_subject: str
    email_body: str
    email_send: str