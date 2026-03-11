from model.ChatTwinModel import ChatTwin
from vo.MyBio import mybio
from vo.Metadata import Metadata
import logging
from embeddings.ChonkieSemanticEmbedding import ChonkieSemanticEmbedding
from services.VectorDBService import VectorDBService
from services.DocumentService import DocumentService
from services.RedisService import RedisService
from utils.SystemConfig import config
from model.ChatTwinModel import ChatTwin

logger = logging.getLogger(__name__)

class UIService():

    def __init__(self):
        print (f"System prompt loading:")
        self.redis_service = RedisService()
        self.system_prompt: str = mybio["text"]
        print (f"System prompt loaded: {self.system_prompt[:100]}...")


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
    
    def chatToTwin(self, prompt : str, session_id: str) -> str:
        redis_key = f"{RedisService.CHAT_TWIN}:{session_id}"

        # Get message history from Redis
        messages = self.redis_service.get_message_history(redis_key)

        # Initialize ChatTwin
        chat_twin = ChatTwin(model_role_type=self.system_prompt)
        
        if messages:
            chat_twin.set_messages(messages)
        else:
            logger.info(f"New session started for ID: {session_id}")
        
        number_of_calls = chat_twin.num_calls

        # Guardrails check
        can_proceed, err_message = self.input_guardrails(chat_twin, prompt, number_of_calls)

        if not can_proceed:
            # Save state if needed (e.g. if guardrails add a message)
            self.redis_service.set_message_history(redis_key, chat_twin.get_messages())
            return err_message

        try:
            response = chat_twin.chat(prompt)
            # Save updated message history back to Redis
            self.redis_service.set_message_history(redis_key, chat_twin.get_messages())
            return response
        except Exception as e:
            logger.error(f"Error during chat in session {session_id}: {e}", exc_info=True)
            # We still save the history in case some progress was made
            self.redis_service.set_message_history(redis_key, chat_twin.get_messages())
            raise e

