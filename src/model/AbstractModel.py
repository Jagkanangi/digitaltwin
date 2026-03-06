from abc import ABC, abstractmethod
from dotenv import load_dotenv
from openai.types.chat import ChatCompletionMessage
import logging

logger = logging.getLogger(__name__)

class AbstractChatClient(ABC):
    """
    Abstract class for all orchestrators/Facade that call models. This class helps with access to messages and history
    The concrete class needs to implement the chat method. The chat method controls the flow between the user and the LLM
    it should return the message that was sent by the called LLM. 
    The initialize_client method is responsible for setting up the LLM client (e.g., OpenAI, LiteLLM) or and is called at the the time of object creation
    """

    def __init__(self, model_name, model_key, model_role_type = "You are an assistant"):
        load_dotenv()
        self.model_name = model_name
        self.model_key = model_key
        self.messages = []
        self.model_role_type = model_role_type
        self.SYSTEM_ROLE = "system"
        self.USER_ROLE = "user"
        self.ASSISTANT_ROLE = "assistant"
        self.TOOL_ROLE = "tool"
        self.initialize_client()

    @abstractmethod
    def initialize_client(self):        
        pass 
    
    @abstractmethod
    def chat(self, prompt, temperature = 0, max_tokens = 500, model = None) -> str:
        pass

    # convenience method to create role type tool and add it to the message history
    def add_tool_message(self, assistant_msg : ChatCompletionMessage, content : str):
        self.messages.append(assistant_msg.model_dump())
        if(assistant_msg.tool_calls is not None and len(assistant_msg.tool_calls) > 0):
            self.messages.append(
                {"role": self.TOOL_ROLE,
                "tool_call_id": assistant_msg.tool_calls[0].id,
                "content": content
                }
            )
    # convenience method to add text to message history
    def add_message(self, role, content):
        # if(role == self.USER_ROLE):
        #     self.filterMessageForHarmfulness(content)
        if(len(self.messages) == 0): # if this is the first message, add the system role
            self.messages.append({"role":self.SYSTEM_ROLE, "content": self.model_role_type})
        self.messages.append({"role": role, "content": content})

    def clear_messages(self):
        self.messages = []
    # def set_history(self, history : list[str]) -> str:
    #     self.messages = for history
    def remove_rag(self):
        if len(self.messages) < 2:
            return

        message_to_alter = self.messages[-2]
        if isinstance(message_to_alter, dict) and 'content' in message_to_alter:
            content = message_to_alter['content']
            rag_tag_position = content.lower().find('<rag>')
            if rag_tag_position != -1:
                message_to_alter['content'] = content[:rag_tag_position].strip()
    # convenience method to get all messages
    def get_messages(self):
        return self.messages
    
    def set_messages(self, messages):
        self.messages = messages
    
    # convenience method to get the last message of a specific role
    def get_last_message(self, role = None) -> str:
        if(role is None):
            role = self.SYSTEM_ROLE
        last_message = ""
        if self.messages:
            for message in reversed(self.messages):
                if(isinstance(message, dict)):
                    if message['role'] == role:
                        last_message = message["content"]
                        break
        return last_message
    # print all messages
    def print_messages(self):
        for message in self.messages:
            logger.info(f"{message['role']}: {message['content']}")

    # print the last message that was recieved from the LLM 
    def print_last_message(self, role = "system"):
        last_message = self.get_last_message(role)
        if last_message:
            logger.info(f"{role}: {last_message}")
        else:
            logger.info(f"No {role} messages found.")
    
    def filterMessageForHarmfulness(self, message : str):
        """
        Filters a message for harmful content using the OpenAI moderation API.

        Args:
            message: The message to filter.

        Raises:
            ValueError: If harmful content is detected in the message.
        """
        import openai as client
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        client.api_key = api_key        
        response = client.moderations.create(
            model="omni-moderation-latest",
            input=message,
        )
        flagged : bool = False

        output = response.results
        for moderation_result in output:
            # You can see exactly why it was flagged:
            for category, is_flagged in moderation_result.categories:
                if is_flagged:
                    logger.warning(f"- Flagged for: {category}")
                    if(flagged == False):
                        flagged = True
        if(flagged):
            raise ValueError("Harmful content detected in message.")
    



    