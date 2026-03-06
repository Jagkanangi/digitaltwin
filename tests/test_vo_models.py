import pytest
from pydantic import ValidationError
from src.vo.Models import Weather, GeneralChat, Contact, WeatherReport, Choices, SessionState, SearchResult
from src.vo.Metadata import Metadata

def test_weather_model():
    data = {"city": "London"}
    weather = Weather(**data)
    assert weather.city == "London"

def test_general_chat_model():
    data = {"message": "Hello"}
    chat = GeneralChat(**data)
    assert chat.message == "Hello"

def test_contact_model():
    data = {"name": "John Doe", "email": "john.doe@example.com"}
    contact = Contact(**data)
    assert contact.name == "John Doe"
    assert contact.email == "john.doe@example.com"
    assert contact.phone is None

def test_weather_report_model():
    data = {
        "city": "London",
        "country": "UK",
        "temperature_2m": 15.0,
        "relative_humidity_2m": 80
    }
    report = WeatherReport(**data)
    assert report.city == "London"
    assert report.temperature == 15.0
    assert report.humidity == 80
    assert report.units == "Celsius"

def test_choices_model():
    data = {"choice": {"unknown_field": "some_value"}}
    # This is not a valid choice, as it doesn't match GeneralChat, Contact, or Weather
    with pytest.raises(ValidationError):
        Choices(**data)

    data = {"choice": {"message": "Hi there"}}
    choices = Choices(**data)
    assert isinstance(choices.choice, GeneralChat)

    data = {"choice": {"city": "Tokyo"}}
    choices = Choices(**data)
    assert isinstance(choices.choice, Weather)
    
    data = {"choice": {"name": "Jane Doe", "email": "jane.doe@example.com"}}
    choices = Choices(**data)
    assert isinstance(choices.choice, Contact)


def test_session_state_model():
    session = SessionState()
    session.add_to_session("key1", "value1")
    assert session.get_from_session("key1") == "value1"
    session.add_to_session("key2", 123)
    assert session.get_from_session("key2") == 123
    session.remove_from_session("key1")
    assert session.get_from_session("key1") is None
    all_data = session.get_all_session_data()
    assert all_data == {"key2": 123}
    session.clear_session()
    assert session.get_all_session_data() == {}

def test_search_result_model():
    metadata = Metadata(root={"source": "test_source"})
    data = {
        "id": "123",
        "document": "test document",
        "metadata": metadata,
        "distance": 0.5
    }
    result = SearchResult(**data)
    assert result.id == "123"
    assert result.document == "test document"
    assert result.metadata.root["source"] == "test_source"
    assert result.distance == 0.5
