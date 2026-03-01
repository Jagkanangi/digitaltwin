from model.ChatTwinModel import ChatTwin
from vo.MyBio import mybio
from vo.Metadata import Metadata
import logging
from embeddings.ChonkieSemanticEmbedding import ChonkieSemanticEmbedding
from services.VectorDBService import VectorDBService
from services.DocumentService import DocumentService
from utils.SystemConfig import config
logger = logging.getLogger(__name__)

class UIService():

    def __init__(self):
        pass

    def input_guardrails(self, chat_twin : ChatTwin, message : str, number_of_calls : int) -> tuple[bool, str]:
        message = message.replace("<info>", "")
        message = message.replace("</info>", "")
        can_continue : bool = True
        err_message : str = "No anomally detected."
        try:
            chat_twin.filterMessageForHarmfulness(message)
        except ValueError as e:
            logger.warning(f"Harmful or abusive content detected in message: {e}")
            can_continue = False
            err_message = "Harmful or abusive content detected in message."
        # if(len(message) > 5000):
        #     can_continue = False
        #     err_message = "Message is too long. If you want to know more about me, please give me your email and optionally a phone number. "
        if(chat_twin.num_calls > 100):
            can_continue = False
            err_message = "I know you would like to know more about me. Please give me your email and optionally a phone number and I will get in touch with you"
        return can_continue, err_message


    def process_startup_files(self):
        vector_db_service = VectorDBService()
        document_service = DocumentService(ChonkieSemanticEmbedding, vector_db_service)
        document_service.process_and_embed_directory(config.persona_settings.persona_collection_name)
        logger.info("Embedding all files from the data directory is complete.")
