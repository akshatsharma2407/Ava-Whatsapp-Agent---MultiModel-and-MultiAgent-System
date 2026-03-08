import os
import traceback
from io import BytesIO
from typing import Dict
import httpx
from fastapi import APIRouter, Request, Response, BackgroundTasks
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from ai_companion.graph.graph import create_workflow_graph
from ai_companion.settings import settings
from ai_companion.modules.image.image_to_text import ImageToText
from ai_companion.modules.speech.speech_to_text import SpeechToText
from ai_companion.modules.speech.text_to_speech import TextToSpeech

whatsapp_router = APIRouter()

WHATSAPP_TOKEN = settings.WHATSAPP_TOKEN
WHATSAPP_PHONE_NUMBER_ID = settings.WHATSAPP_PHONE_NUMBER_ID
WHATSAPP_VERIFY_TOKEN = settings.WHATSAPP_VERIFY_TOKEN

speech_to_text = SpeechToText()
image_to_text = ImageToText()

def download_media(media_id: str) -> bytes:
    """Download media from Whatsapp"""
    media_metadata_url = f"https://graph.facebook.com/v21.0/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}

    with httpx.Client() as client:
        metadata_response = client.get(media_metadata_url, headers=headers)
        metadata_response.raise_for_status()
        download_url = metadata_response.json().get("url")

        media_response = client.get(download_url, headers=headers)
        media_response.raise_for_status()
        return media_response.content

def process_audio_message(message: Dict) -> str:
    """Download and transcribe audio message"""
    audio_id = message["audio"]["id"]

    audio_bytes = download_media(audio_id)

    audio_buffer = BytesIO(audio_bytes)
    audio_buffer.seek(0)
    audio_data = audio_buffer.read()

    return speech_to_text.transcribe(audio_data)

def upload_media(media_content: bytes, mime_type: str) -> str:
    """Upload media to WhatApp server and get an ID back"""
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    files = {"file": ("upload_file", media_content, mime_type)}
    data = {"messaging_product": "whatsapp", "type":mime_type}

    with httpx.Client() as client:
        response = client.post(
            f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}/media",
            headers=headers,
            files=files,
            data=data
        )
        result = response.json()
    
    if "id" not in result:
        raise Exception("Failed to upload media")
    return result["id"]

def process_and_reply(change_value: dict):
    """Heavy AI processing happens here in the background without making Meta wait!"""
    try:
        message = change_value['messages'][0]
        from_number = message['from']
        session_id = from_number

        content = ""
        if message["type"] == 'audio':
            content = process_audio_message(message)
        elif message["type"] == "image":
            content = message.get("image", {}).get("caption", "")
            image_bytes = download_media(message["image"]["id"])
            try:
                description = image_to_text.analyze_image(
                    image_bytes,
                    "Please describe what you see in this image in the context of our conversation"
                )
                content += f"\n[Image Analysis: {description}]"
            except Exception as e:
                print(f"Failed to analyze image: {str(e)}")
        else:
            content = message['text']['body']
        
        with SqliteSaver.from_conn_string(settings.SHORT_TERM_MEMORY_DB_PATH) as short_tearm_memory:
            graph_builder = create_workflow_graph()
            graph = graph_builder.compile(checkpointer=short_tearm_memory)
            graph.invoke(
                    input={'messages' : [HumanMessage(content=content)]},
                    config={'configurable' : {'thread_id' : session_id}}
            )
            output_state = graph.get_state(config={'configurable' : {'thread_id' : session_id}})
            
            workflow = output_state.values.get('workflow', 'conversation')
            response_message = output_state.values['messages'][-1].content
        
        success = False 

        if workflow == "audio":
            audio_buffer = output_state.values.get("audio_buffer")
            success = send_response(from_number, response_message, "audio", audio_buffer)
        
        elif workflow == "image":
            image_path = output_state.values.get("image_path")
            with open(image_path, "rb") as f:
                image_data = f.read()
            success = send_response(from_number, response_message, "image", image_data)

        else:
            success = send_response(from_number, response_message, "text")
        
        if not success:
            print(" Failed to send outgoing message to Meta.")
            
    except Exception as e:
        print("\n" + "="*50)
        print(" CRASH IN BACKGROUND TASK ")
        traceback.print_exc()
        print("="*50 + "\n")


@whatsapp_router.api_route('/whatsapp_response', methods=['GET', 'POST'])
async def whatsapp_handler(request: Request, background_tasks: BackgroundTasks): 
    """Handles incoming messages and instantly returns 200 OK to Meta"""

    if request.method == 'GET':
        params = request.query_params
        if params.get('hub.verify_token') == WHATSAPP_VERIFY_TOKEN:
            return Response(content=params.get('hub.challenge'), status_code=200)
        return Response(content='Verification token mismatch', status_code=403)
    
    try:
        data = await request.json()
        change_value = data['entry'][0]['changes'][0]['value']
        
        if "messages" in change_value:
            background_tasks.add_task(process_and_reply, change_value)
            
            # immediately send Meta the receipt so it doesn't retry!
            return Response(content='Message Acknowledged', status_code=200)
        
        elif 'statuses' in change_value:
            return Response(content='Status Update Recieved', status_code=200)
        
        else:
            return Response(content='Unknown event type', status_code=400)
        
    except Exception as e:
        print("\n" + "="*50)
        print(" CRASH IN WHATSAPP HANDLER ")
        traceback.print_exc()
        print("="*50 + "\n")
        return Response(content='Internal Server error', status_code=500)


def send_response(from_number: str, response_text: str, message_type: str = 'text', media_content: bytes = None):
    """Send response to user via WhatsApp API"""

    headers = {
        'Authorization' : f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type" : "application/json"
    }

    if message_type in ['audio', 'image']:
        try:
            mime_type = "audio/mpeg" if message_type == "audio" else "image/png"
            media_id = upload_media(media_content, mime_type)

            json_data = {
                "messaging_product" : "whatsapp",
                "to" : from_number,
                "type" : message_type,
                message_type: {"id": media_id}
            }

            if message_type == "image":
                json_data["image"]["caption"] = response_text
        
        except Exception as e:
            print(f"media upload failed, falling back to text: {e}")
            message_type = "text"

    
    if message_type in ['text']:
        json_data = {
            "messaging_product" : "whatsapp",
            "to" : from_number,
            'type' : "text",
            "text" : {"body" : response_text}
        }
    
    with httpx.Client() as client:
        response = client.post(
            f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}/messages",
            headers=headers,
            json=json_data,
        )

        if response.status_code != 200:
            print("\n" + "!"*50)
            print(" META API ERROR ")
            print(f"Status Code: {response.status_code}")
            print(f"Meta's Response: {response.text}")
            print("!"*50 + "\n")
    
    return response.status_code == 200