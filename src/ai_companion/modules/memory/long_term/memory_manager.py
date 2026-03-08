import uuid
from datetime import datetime
from typing import List, Optional
from ai_companion.core.prompts import MEMORY_ANALYSIS_PROMPT
from ai_companion.modules.memory.long_term.vector_store import get_vector_store
from langchain_core.messages import BaseMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from ai_companion.settings import settings

class MemoryAnalysis(BaseModel):
    """Result of analyzing a message for memory-worthy content"""

    is_important: bool = Field(description="Whether the message is important enough to be stored in memory")
    formatted_memory: Optional[str] = Field(description='The formatted memory to be stored')

class MemoryManager:
    """Manager class for handling long term memory operations"""

    def __init__(self):
        self.vector_store = get_vector_store()
        self.llm = ChatGroq(
            model=settings.SMALL_TEXT_MODEL_NAME,
            api_key=settings.GROQ_API_KEY1,
            temperature=0.1,
            max_retries=2
        ).with_structured_output(MemoryAnalysis)
    
    def _analyze_memory(self, message: str):
        """Analyze a message to determine importance and format if needed"""
        prompt = MEMORY_ANALYSIS_PROMPT.format(message=message)
        return self.llm.invoke(prompt)
    
    def extract_and_store_memories(self, message: BaseMessage):
        if message.type != 'human':
            return
        
        analysis : MemoryAnalysis = self._analyze_memory(message.content)

        if analysis.is_important and analysis.formatted_memory:
            similar = self.vector_store.find_similar_memory(analysis.formatted_memory)

            if similar:
                return
        
            self.vector_store.store_memory(
                text=analysis.formatted_memory,
                metadata={
                    'id': str(uuid.uuid4()),
                    'timestamp' : datetime.now().isoformat()
                }
            )
    
    def get_relevant_memories(self, context: str):
        """Retrieve relevant memoreis based on the current context"""
        memories = self.vector_store.search_memories(context, k=settings.MEMORY_TOP_K)
        return [memory.text for memory in memories]
    
    def format_memories_for_prompt(self, memories: List[str]):
        """Format retrieved memories as bullet points"""
        if not memories:
            return ""
        
        return '\n'.join(f"- {memory}" for memory in memories)
    
def get_memory_manager():
    """Get a MemoryManager instance"""
    return MemoryManager()