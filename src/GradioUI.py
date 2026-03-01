import gradio as gr
from model.ChatTwinModel import ChatTwin
from vo.Models import SessionState
from vo.MyBio import mybio
import logging
from utils.LoggerInit import init as initialize_logger
from services.UIService import UIService
initialize_logger()
UIService().process_startup_files()



# Get a logger for this module
logger = logging.getLogger(__name__)
#
system_prompt : str = mybio["text"]

def gradio_function(message : str, _, session_state):
    
    ui_service = UIService()
    chat_twin = session_state.get_from_session(SessionState.MODEL_KEY)
    number_of_calls = chat_twin.num_calls

    (can_proceed, err_message)= ui_service.input_guardrails(chat_twin, message, number_of_calls)
    # value_in_dictionary = encode_and_compare(message)
    # message = value_in_dictionary +" If the info tag is present and it is relevant to the question thenyou can respond to the question using the text between the info tag. Do not mention the info tag in your response. " + message 
    # print(message)

    return_str = ""
    if(can_proceed):
        return_str = chat_twin.chat(prompt=message)
    else:
        return_str = err_message
    return return_str

def create_initial_state():
    logger.info("New user session started.")
    # This function runs EVERY TIME a new user opens the page
    new_session = SessionState()
    # Saving session so I can retrieve history without depending on the UI. 
    new_session.add_to_session(
        SessionState.MODEL_KEY, 
        ChatTwin(model_role_type=system_prompt)
    )
    return new_session

with gr.Blocks() as chat_interface:
    state_object = gr.State(value=create_initial_state)

    gr.ChatInterface(
            fn=gradio_function,
            additional_inputs=[state_object] # Matches the 3rd arg in gradio_function
      )
if __name__ == "__main__":
    chat_interface.launch(inbrowser=True)
 

#