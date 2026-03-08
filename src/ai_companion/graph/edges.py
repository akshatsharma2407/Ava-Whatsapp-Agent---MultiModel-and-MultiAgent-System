from langgraph.graph import END
from typing import Literal
from ai_companion.graph.state import AICompanionState, SQLWorkflowState
from ai_companion.settings import settings

def should_summarize_conversation(state: AICompanionState):
    messages = state['messages']

    if len(messages) > settings.TOTAL_MESSAGES_SUMMARY_TRIGGER:
        return 'summarize_conversation_node'
    return END

def select_workflow(state: AICompanionState):
    workflow = state['workflow']

    if workflow == "image":
        return "image_node"

    elif workflow == "audio":
        return "audio_node"

    else:
        return "conversation_node"

def decision_router(state: SQLWorkflowState):
    if state['intent'] == 'Ambiguous':
        return 'Ambiguous'
    elif state['intent'] == 'Unsafe':
        return 'Unsafe'
    else:
        return 'Valid'

def should_we_loop(state: SQLWorkflowState):
    if state['feedback'] and state['retry_count'] < 3:
        return 'rewrite'
    elif state.get('email', ''):
        return 'sales_agent'
    else:
        return 'back'