from model.AbstractModel import AbstractChatClient
from externalservices.Pushover import PushOver
from instructor import Instructor, from_litellm, from_provider
from functools import singledispatchmethod
from litellm import completion
from externalservices.Weather import WeatherService
from typing import List, Optional
from decorators.AutoLog import log_vo
import logging
from threading import Lock
# from pydantic import BaseModel, Field
from vo.Models import GeneralChat, Weather, Contact, Choices
from utils.SystemConfig import config
from services.VectorDBService import VectorDBService
# Initialize logger for this module
logger = logging.getLogger(__name__)
    
class ChatTwin(AbstractChatClient):
    """
    ChatTwin is the central orchestration model for the ChatTwin application.
    
    DESIGN PATTERN: Orchestrator / Facade
    This class orchestrates interactions between:
    1. LLM (via Litellm & Instructor)
    2. Vector Database (RAG - Retrieval Augmented Generation)
    3. External Services (Weather, Pushover)
    
    It uses the 'instructor' library to enforce structured output from the LLM using Pydantic models.
    """
    _client_instance: Optional[Instructor] = None
    _client_lock = Lock()

    def __init__(self, model_name=config.system.models.llm_model, model_key="", model_role_type="You are an assistant"):
        """
        Initializes the ChatTwin model.

        Args:
            model_name (str): The identifier for the LLM (e.g., openai/gpt-4).
            model_key (str): API key for the model provider.
            model_role_type (str): The system prompt defining the AI's persona.
        """
        super().__init__(model_name, model_key, model_role_type=model_role_type)
        self.num_calls = 0


    def initialize_client(self):
        """
        Initializes the 'instructor' client as a singleton.
        
        The instructor library wraps the litellm completion call, enabling the use of 
        'response_model' to get validated Pydantic objects instead of raw JSON.
        """
        self.vector_db_service = VectorDBService()
        
        if ChatTwin._client_instance is None:
            with ChatTwin._client_lock:
                if ChatTwin._client_instance is None:
                    try:
                        ChatTwin._client_instance = from_litellm(completion)
                        logger.info("Instructor client initialized successfully as a singleton.")
                    except Exception as e:
                        logger.error(f"Failed to initialize instructor client: {e}", exc_info=True)
                        raise
        
        self.client = ChatTwin._client_instance

    @singledispatchmethod    
    def process_llm_tool_call(self, bm, completion) -> bool:
        """
        DESIGN PATTERN: Single Dispatch (Polymorphism)
        
        This method acts as a router for different tool call types returned by the LLM.
        The @singledispatchmethod allows us to register specific handlers for different 
        Pydantic types (Weather, Contact, GeneralChat) without complex if-else blocks.
        
        Default implementation handles unknown or unregistered types.
        """
        logger.warning(f"No specific tool call handler for type: {type(bm).__name__}")
        self.add_tool_message(completion.choices[0].message, "I cannot find the information for this request. Please try again.")
        return True

    @process_llm_tool_call.register(GeneralChat)
    @log_vo
    def _(self, general_chat, completion) -> bool:
        """
        Handler for standard conversational responses.
        Returns False to indicate that no further LLM callback is needed for tool processing.
        """
        try:
            content = general_chat.message
            super().add_message(self.ASSISTANT_ROLE, content)
            return False
        except Exception as e:
            logger.error(f"Error processing general chat tool call: {e}", exc_info=True)
            return True


    @process_llm_tool_call.register(Weather)
    @log_vo
    def _(self, weather, completion) -> bool:
        """
        Handler for Weather tool calls.
        
        FLOW:
        1. Extract city from the 'weather' Pydantic model.
        2. Call WeatherService to get real-time data.
        3. Feed the data back into the conversation context as a 'tool' message.
        4. Return True to signal that the LLM should be called again to synthesize the final answer.
        """
        try:
            if(weather is None):
                logger.warning("Weather tool call received with None object.")
                return True 
            
            if(weather.city is None or weather.city.strip() == ""): 
                logger.warning("Weather tool call received with empty city name.")
                return True 
            else :
                weather_service = WeatherService()
                weather_report = weather_service.get_weather_object(city_name=weather.city)

                if(weather_report is not None):
                    # Injecting tool result into context. The LLM will use this in the next pass.
                    self.add_tool_message(completion.choices[0].message, f"The weather in {weather_report.city} is {weather_report.temperature} degrees Celsius with {weather_report.humidity}% humidity.")
                else:
                    logger.warning(f"Weather report not found for city: {weather.city}")
                    self.add_tool_message(completion.choices[0].message, f"I cannot find the information for {weather.city}")
            return True # Signal callback needed
        except Exception as e:
            logger.error(f"Error processing weather tool call: {e}", exc_info=True)
            return True

    @process_llm_tool_call.register(Contact)
    @log_vo
    def _(self, contact, completion) -> bool:
        """
        Handler for Contact tool calls.
        
        FLOW:
        1. Extract contact details.
        2. Send a notification via PushOver.
        3. Inform the LLM that the notification was sent.
        4. Return True to trigger the final natural language response to the user.
        """
        try:
            if(contact is None):
                logger.warning("Contact tool call received with None object.")
                return True 
            if(contact.name is None or contact.name.strip() == "" or contact.email is None or contact.email.strip() == ""):
                logger.warning(f"Contact tool call received with incomplete data: {contact}")
                return True 

            else:
                PushOver().send_message(f"The person {contact.name} would like to get in touch with you. His or her email is {contact.email} and their phone number is {contact.phone}")
                self.add_tool_message(completion.choices[0].message, "Let the user know you will connect with them shortly and thank the user for their interest.")
            return True # Signal callback needed
        except Exception as e:
            logger.error(f"Error processing contact tool call: {e}", exc_info=True)
            return True


    def chat(self, prompt : str, temperature=0, max_tokens=500, model=None) -> str:
        """
        The primary entry point for user interaction.
        
        LOGIC FLOW:
        1. Call a local llm to classify intent and set the temperature 
        2. RAG PHASE: If enabled, query VectorDB and prepend context to the prompt.
        3. LLM PHASE 1 (Structured): Send prompt to LLM, requesting a list of 'Choices' (tool calls).
        4. DISPATCH PHASE: Iterate through returned choices and execute corresponding tool handlers.
        5. CALLBACK PHASE: If any tool was called, perform a second LLM pass to get a natural language summary.
        6. RETURN: Give the final assistant message back to the UI.
        """
        # Step 1: Intent Classification (using sync litellm client)
        # intent_response, _ = self.intent_provider_client.chat.create_with_completion(
        #         model=f"ollama/{config.system.llm_intent_provider.model}",
        #         api_base=config.system.llm_intent_provider.host,
        #         messages=[
        #                 {"role": "system", "content": "You are a strict intent classifier. Categorize every message as either PROFILE or GENERAL.Never provide conversational text."},
        #                 {"role": "user", "content": prompt}],
        #                 response_model=Classifier)
        print("Response from ")
        # Step 2: Retrieval Augmented Generation (RAG)
        if(config.system.llm_settings.llm_rag_enabled):
            rag_text = self.vector_db_service.query(prompt, config.persona_settings.persona_collection_name)
            if(rag_text is not None):
                prompt += f"\n\nContext from knowledge base:\n{rag_text}"

        # Step 2: Add user message to conversation history
        self.add_message(self.USER_ROLE, prompt)


        if model is None:
            model = self.model_name
        try:             
            # Step 2: First LLM pass with structured output enforcement
            if self.client is None:
                self.client._turn_on_debug()
            logger.info(f"Sending prompt to LLM with model {model}. Prompt: {self.get_messages()}")
            response, completion = self.client.chat.create_with_completion(
                model=model,
                messages=self.get_messages(),
                response_model=List[Choices],
                max_retries=2)
            
            call_back_LLM : bool = False

            # Step 3: Handle the tool calls
            for choices in response:
                # Single dispatch routing happens here
                should_call_back =self.process_llm_tool_call(choices.choice, completion)
                if(call_back_LLM == False and should_call_back == True):
                    call_back_LLM = True                     
            
            # Step 4: Final pass if tools were used
            if(call_back_LLM):
                chat_response = self.client.chat.completions.create(model=model, messages=self.get_messages(), response_model=GeneralChat)
                if isinstance(chat_response, GeneralChat):
                    self.add_message(self.ASSISTANT_ROLE, chat_response.message)
            
            self.num_calls += 1
            
        except Exception as e:
            logger.error(f"An error occurred in chat loop: {e}", exc_info=True)
            return """This is embarrasing. I am an AI assistant who ever so often start hallucinating or stop following instruction.\
              I try my best not to do that but you caught me red handed. I have lost my marbles.\
              Can you please refresh and try again? If I still fail you can you please come back later?"""
              
        return self.get_last_message(role=self.ASSISTANT_ROLE)
