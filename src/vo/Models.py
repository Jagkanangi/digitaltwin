from pydantic import BaseModel, Field, AliasChoices
from typing import Union, Any
from vo.Metadata import Metadata

__all__ = ["Weather", "GeneralChat", "Contact", "WeatherReport", "Choices", "SessionState", "SearchResult"]

class Classifier(BaseModel):
   category: str # "PROFILE" or "GENERAL"
class Weather(BaseModel):
    """
    Represents a request for weather information for a specific city.
    """
    city: str = Field(description="Name of the city.")

class GeneralChat(BaseModel):
    """
    Represents a general chat message.
    """
    message : str = Field(description="Response to any user message by the LLM")

class Contact(BaseModel):
    """
    Represents a contact request from a user. Obtain Name, Email and optionally a phone number from the user before populating this object or calling this Tool.
    """
    name : str = Field(description="Name of the user")
    email : str = Field(description="Email of the user")
    phone : str | None = Field(default=None, description="Phone number of the user")



class WeatherReport(BaseModel):
    """
    Represents a weather report with city, country, temperature, humidity, and units.
    Uses Pydantic for data validation and serialization.
    """
    city: str = Field(description="The name of the city for the weather report.")
    country: str = Field(description="The country of the city for the weather report.")
    temperature: float = Field(..., alias="temperature_2m")
    humidity: int = Field(..., alias="relative_humidity_2m")
    units: str = Field(default="Celsius", description="The temperature units.")

    class Config:
        populate_by_name = True # Allows using both alias and field name


class Choices(BaseModel):
    """
    A Pydantic model that can represent either a general chat message or a weather request.
    This is used to handle different types of responses from the language model.
    """
    choice : Union[GeneralChat, Contact, Weather] = Field(description="A union of GeneralChat, Contact, or Weather, representing the chosen action.")

class SessionState():


    MODEL_KEY = "Model_Key"
    NUMBER_OF_CALLS_KEY = "Number_of_Calls_Key"
    
    def __init__(self):
        self.state_dict = {}

    def add_to_session(self, key : str, value : Any):
        self.state_dict[key] = value

    def get_from_session(self, key : str) -> Any:
        return self.state_dict.get(key)

    def remove_from_session(self, key : str):
        self.state_dict.pop(key, None)
    
    def get_all_session_data(self) -> dict:
        return self.state_dict

    def clear_session(self):
        self.state_dict = {}

class SearchResult(BaseModel):
    """
    Represents a single search result from the vector database.
    """
    id: str
    document: str
    metadata: Metadata | None = None
    distance: float | None = Field(default=None, validation_alias=AliasChoices('distance', 'score', 'rank'))

    class Config:
        populate_by_name = True
