import os
from uuid import uuid4
from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig
from ai_companion.graph.state import AICompanionState, SQLWorkflowState
from ai_companion.graph.utils.chains import (
    get_router_chain,
    get_character_response_chain,
    get_intent_finder_chain,
    get_SQL_generator_chain,
    get_sales_chain
)
from ai_companion.graph.utils.helpers import (
    get_chat_model,
    get_text_to_image_module,
    get_text_to_speech_module,
    get_db,
    IntentStructure,
    RouterResponse,
    SQLStructure
)
from ai_companion.graph.tools import run_query, send_sales_email
from ai_companion.modules.memory.long_term.memory_manager import get_memory_manager
from ai_companion.modules.schedules.context_generation import ScheduleContextGenerator
from ai_companion.settings import settings

def router_node(state: AICompanionState):
    chain = get_router_chain()
    response: RouterResponse = chain.invoke({'messages': state['messages'][-settings.ROUTER_MESSAGES_TO_ANALYZE:]})
    return  {'workflow': response.response_type}

def conversation_node(state: AICompanionState, config: RunnableConfig):
    current_activity = ScheduleContextGenerator.get_currect_activity()
    print(current_activity)
    memory_context = state.get("memory_context", "")
    chain = get_character_response_chain(from_conversation_node=True,summary=state.get('summary', ''))
    response = chain.invoke(
        {
            'messages': state['messages'],
            'current_activity': current_activity,
            'memory_context': memory_context
        },
        config=config
    )
    return {'messages' : response}

def find_intent(state: SQLWorkflowState):
    chain = get_intent_finder_chain()
    result : IntentStructure = chain.invoke(
        {'question' : state['messages']}
    )
    print(f'the intent is - {result.decision} and reasoning behind this is - {result.explaination}')

    return {"intent" : result.decision, 'email' : result.email}

def Ambiguous_Node(state: SQLWorkflowState):
    response = f"The question asked is ambiguous, because of {state['reason_for_intent']}"
    return {'messages' : response}

def Unsafe_Node(state: SQLWorkflowState):
    response = f"Cannot generate and execute the SQL as it involve high stake decision because of following reason {state['reason_for_intent']}"
    return {"messages" : response}

def SQL_Generator(state: SQLWorkflowState):
    chain = get_SQL_generator_chain()
    question = ''

    if state.get('feedback'):
        question += f"\nYour previous query failed, fix it based on this : {state['feedback']}"
    
    question += f"\n\n question is {state['messages']}"

    response: SQLStructure = chain.invoke(
        {
            'schema' : get_db().get_table_info(),
            'question' : question
        }
    )

    current_retries = state.get('retry_count', 0)

    return {'reason_behind_generated_sql': response.explaination, 'generated_sql': response.SQL_query, 'retry_count' : current_retries + 1}

def Evaluator(state: SQLWorkflowState):
    sql = state['generated_sql']

    if any(word in sql.upper().split() for word in ['CREATE', 'DROP', 'ALTER', 'TRUNCATE', 'DELETE', 'INSERT', 'UPDATE', 'GRANT', 'REVOKE']):
        return {'feedback': f"Safety violation: command you have written is -> {sql} \n  But you cannot write the query with the DML,DDL, DCL commands, re-write using SELECT"}
    
    try:
        result = run_query.invoke(sql)
    except Exception as e:
        return {'feedback' : f'There is error while executing this SQL command \n Error - {e}'}
    else:
        if len(result) > 500:
            return {
                'feedback' : f"the query returned too much data. To prevent server overload, rewrite the query to return fewer rows with strictly the LIMIT clause with only 10 rows, no matter how many rows, the user is asking.",
                'extra_info' : "Because the Database is returning more than 50 rows, hence we are cutting down the result, because server can't handle sending large data results"
            }
        return {'feedback' : None, 'result' : result}

def sales_node(state: SQLWorkflowState):
    chain = get_sales_chain()
    draft = chain.invoke(
        {
            'result' : state['result'],
            'message': state['messages']
        }
    )
    return {
        "email_subject": draft.subject,
        "email_body" : draft.body
    }

def email_sender_node(state: SQLWorkflowState):
    result = send_sales_email.invoke(
        {
          'recipient_email' : state['email'],
          'subject' :  state['email_subject'],
          'body' : state['email_body']
        }
    )
    
    return {'email_send' : result}

def image_node(state: AICompanionState, config: RunnableConfig):
    current_activity = ScheduleContextGenerator.get_currect_activity()
    memory_context = state.get("memory_context", '')

    chain = get_character_response_chain(state.get("summary", ""))
    text_to_image_module = get_text_to_image_module()

    scenario = text_to_image_module.create_scenario(state['messages'][-5:])
    os.makedirs('generated_images', exist_ok=True)
    img_path = f"generated_images/image_{str(uuid4())}.png"
    text_to_image_module.generate_image(scenario.image_prompt, img_path)

    scenario_message = HumanMessage(content=f"<image attacted by ava generated from prompt: {scenario.image_prompt}>")
    updated_messages = state['messages'] + [scenario_message]

    response = chain.invoke(
        {
            "messages" : updated_messages,
            "current_activity" : current_activity,
            "memory_context": memory_context
        },
        config
    )

    return {"messages": response, "image_path": img_path}

def audio_node(state: AICompanionState, config: RunnableConfig):
    current_activity = ScheduleContextGenerator.get_currect_activity()
    memory_context = state.get("memory_context", "")

    chain = get_character_response_chain(state.get("summary", ""))
    text_to_speech_module = get_text_to_speech_module()

    response = chain.invoke(
        {
            "messages" : state["messages"],
            "current_activity" : current_activity,
            "memory_context" : memory_context
        },
        config=config
    )

    output_audio = text_to_speech_module.synthesize(response.content)

    return {"messages": response, "audio_buffer": output_audio}

def summarize_conversation_node(state: AICompanionState):
    model = get_chat_model()
    summary = state.get('summary', '')

    if summary:
        summary_message = (
            f"This is summary of the conversation to date between Ava and the user: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
    else:
        summary_message = (
            "Create a summary of the conversation above between Ava and the user. "
            "The summary must be a short description of the conversation so far, "
            "but that captures all the relevant information shared between Ava and the user:"
        )
    
    messages = state['messages'] + [HumanMessage(content=summary_message)]
    response = model.invoke(messages)

    delete_messages = [RemoveMessage(id=m.id) for m in state['messages'][: -settings.TOTAL_MESSAGES_AFTER_SUMMARY]]
    return {'summary' : response.content, "messages": delete_messages}

def memory_extraction_node(state: AICompanionState):
    """Extract and store important information from last message"""
    if not state["messages"]:
        return {}
    
    memory_manager = get_memory_manager()
    memory_manager.extract_and_store_memories(state['messages'][-1])
    return {}

def memory_injection_node(state: AICompanionState):
    """Retrieve and inject relevant memories into the character card"""
    memory_manager = get_memory_manager()

    recent_context = " ".join([m.content for m in state['messages'][-3:]])
    memories = memory_manager.get_relevant_memories(recent_context)

    memory_context = memory_manager.format_memories_for_prompt(memories)

    return {"memory_context": memory_context}

