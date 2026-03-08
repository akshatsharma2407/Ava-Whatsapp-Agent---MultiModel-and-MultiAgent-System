from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from ai_companion.core.prompts import CHARACTER_CARD_PROMPT, ROUTER_PROMPT, INTENT_PROMPT, SQL_GENERATOR_PROMPT, SALES
from ai_companion.graph.utils.helpers import get_chat_model, RouterResponse, SQLStructure
from ai_companion.graph.tools import tools
from ai_companion.graph.utils.helpers import IntentStructure, EmailDraft

def get_router_chain():
    model = get_chat_model(temperature=0.3).with_structured_output(RouterResponse)

    prompt = ChatPromptTemplate.from_messages(
        [('system', ROUTER_PROMPT), MessagesPlaceholder(variable_name="messages")]
    )

    return prompt | model

def get_character_response_chain(summary: str = '',from_conversation_node=False):
    model = get_chat_model()

    if from_conversation_node:
        model = model.bind_tools(tools)

    system_message = CHARACTER_CARD_PROMPT

    if summary:
        system_message += f'\n\n Summary of conversation ealier between Ava and user: {summary}'
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ('system', system_message),
            MessagesPlaceholder(variable_name="messages")
        ]
    )

    return prompt | model

def get_intent_finder_chain():
    model = get_chat_model(from_subgraph=True)
    structued_model = model.with_structured_output(IntentStructure)
    chat_template = ChatPromptTemplate.from_messages(
        [("system", INTENT_PROMPT),
         ("human", "{question}")]  
    )

    return chat_template | structued_model

def get_SQL_generator_chain():
    prompt = ChatPromptTemplate.from_messages(
        [
            ('system', SQL_GENERATOR_PROMPT),
            ('human', 'Here is DATABASE SCHEMA \n\n {schema} \n\n and here is the question for which you need to write SQL query {question}')
        ]
    )
    model = get_chat_model(from_subgraph=True)
    structuredmodel = model.with_structured_output(SQLStructure)
    return prompt | structuredmodel

def get_sales_chain():
    prompt = ChatPromptTemplate.from_template(SALES)
    model = get_chat_model(from_subgraph=True)
    structured_model = model.with_structured_output(EmailDraft)
    return prompt | structured_model