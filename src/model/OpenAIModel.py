import os
import openai as client
import logging

logger = logging.getLogger(__name__)

from AbstractModel import AbstractChatClient

class OpenAIModel(AbstractChatClient):
    def __init__(self, model_name="gpt-3.5-turbo", model_key="", model_role_type="You are an assistant"):
        super().__init__(model_name, model_key, model_role_type=model_role_type)
        self.initialize_client()

    def initialize_client(self):
        """
        Initializes the OpenAI client.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        client.api_key = api_key

    def chat(self, prompt, temperature=0, max_tokens=500, model=None) -> str:
        """
        Gets a completion from the OpenAI API.
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
            """
            some models don't like temperature so if it is not present don't pass it. At some point need to find a way to
            remove this dependency on the caller. 
            """
            if(temperature==0):
                response = client.chat.completions.create(
                    model=model,
                    messages=self.get_messages())
            else:   
                response = client.chat.completions.create(
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
            return "An error occurred during the chat. Response is empty"
        else: 
            return content