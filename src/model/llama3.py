import os
import openai as LLamaClient
from dotenv import load_dotenv
import logging
from utils.SystemConfig import config
logger = logging.getLogger(__name__)

load_dotenv()
from AbstractModel import AbstractChatClient

class llama3(AbstractChatClient):
    def __init__(self, model_name="llama3", model_key="", model_role_type="You are a classifier. "):
        super().__init__(model_name, model_key, model_role_type=model_role_type)
        self.initialize_client()

    def initialize_client(self):
        """
        point to where the server is running. I am getting it from the env file but if it is not present just hardcoding it for now
        """
        lamma_base_url = config.system.llm_settings.llama_host
        self.client = LLamaClient.Client(
                            base_url=lamma_base_url,
                            api_key='ollama', # not required for localhost but need to pass it for the interface to work
                        )
    def chat(self, prompt, temperature=0, max_tokens=500, model=None) -> str:
        """
        Gets a completion from the ollama.
        """
        content : str | None = None
        """
        user can change model but maintain context from the previous conversation
        """
        if model is None:
            model = self.model_name
        """
        add the prompt to the context
        """    
        self.add_message(self.USER_ROLE, prompt)
        response = None
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=self.get_messages(),
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            content = response.choices[0].message.content
            """
            add the response to the context
            """
            self.add_message(self.SYSTEM_ROLE, content)
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            raise e
        if (content is None):
            return "An error occurred during the chat. Response is block"
        else: 
            return content