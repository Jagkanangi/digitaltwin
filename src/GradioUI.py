import gradio as gr
import httpx
import uuid
import logging
from vo.Models import SessionState
from utils.SystemConfig import config
# Get a logger for this module
logger = logging.getLogger(__name__)

REST_SERVICE_URL = config.ui_settings.chat_service_url

default_config = {
    "chat_service_url": "http://localhost:8000/chat"
}

def gradio_function(message: str, history, session_state: SessionState):
    session_id = session_state.get_from_session("session_id")
    
    if not session_id:
        session_id = str(uuid.uuid4())
        session_state.add_to_session("session_id", session_id)

    payload = {
        "message": message,
        "session_id": session_id
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(REST_SERVICE_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "No response received.")
    except httpx.HTTPError as e:
        logger.error(f"Error calling REST service: {e}")
        return f"Error: Could not connect to the chat service. {e}"
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return f"An error occurred: {e}"

def create_initial_state():
    logger.info("New user session started in Gradio UI.")
    new_session = SessionState()
    # Generate a unique session ID for this user session
    session_id = str(uuid.uuid4())
    new_session.add_to_session("session_id", session_id)
    return new_session

with gr.Blocks() as chat_interface:
    state_object = gr.State(value=create_initial_state)

    gr.ChatInterface(
        fn=gradio_function,
        additional_inputs=[state_object]
    )

if __name__ == "__main__":
    chat_interface.launch(inbrowser=True)