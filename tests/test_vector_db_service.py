import pytest
from unittest.mock import patch, MagicMock
from src.services.VectorDBService import VectorDBService

@patch("src.services.VectorDBService.get_vectordb")
def test_vector_db_service_init(mock_get_vectordb):
    mock_db = MagicMock()
    mock_get_vectordb.return_value = mock_db
    
    service = VectorDBService()
    assert service.db == mock_db
    mock_get_vectordb.assert_called_once()

@patch("src.services.VectorDBService.get_vectordb")
def test_vector_db_service_get_db_wrapper(mock_get_vectordb):
    mock_db = MagicMock()
    mock_get_vectordb.return_value = mock_db
    mock_wrapper = MagicMock()
    mock_db.get_db_wrapper.return_value = mock_wrapper
    mock_conn = MagicMock()
    mock_db.get_connection.return_value = mock_conn
    
    service = VectorDBService()
    wrapper = service.get_db_wrapper("test_bucket")
    
    assert wrapper == mock_wrapper
    mock_wrapper.init_bucket.assert_called_once_with(mock_conn, "test_bucket")

@patch("src.services.VectorDBService.get_vectordb")
@patch("src.services.VectorDBService.OpenAIEmbeddingModel")
def test_vector_db_service_query(mock_openai_model, mock_get_vectordb):
    mock_db = MagicMock()
    mock_get_vectordb.return_value = mock_db
    mock_wrapper = MagicMock()
    mock_db.get_db_wrapper.return_value = mock_wrapper
    
    # Mock embedding model
    mock_model_instance = MagicMock()
    mock_openai_model.return_value = mock_model_instance
    mock_model_instance.get_embedding.return_value = [0.1, 0.2]
    
    # Mock search results
    mock_result1 = MagicMock()
    mock_result1.document = "Doc 1"
    mock_result2 = MagicMock()
    mock_result2.document = "Doc 2"
    mock_wrapper.search.return_value = [mock_result1, mock_result2]
    
    service = VectorDBService()
    result = service.query("test query", "test_bucket")
    
    assert """Context : Doc 1
Doc 2
""" in result
    mock_model_instance.get_embedding.assert_called_once_with("test query")
    mock_wrapper.search.assert_called_once_with([[0.1, 0.2]])

@patch("src.services.VectorDBService.get_vectordb")
@patch("src.services.VectorDBService.OpenAIEmbeddingModel")
def test_vector_db_service_query_no_results(mock_openai_model, mock_get_vectordb):
    mock_db = MagicMock()
    mock_get_vectordb.return_value = mock_db
    mock_wrapper = MagicMock()
    mock_db.get_db_wrapper.return_value = mock_wrapper
    
    mock_model_instance = MagicMock()
    mock_openai_model.return_value = mock_model_instance
    mock_wrapper.search.return_value = []
    
    service = VectorDBService()
    result = service.query("test query", "test_bucket")
    
    assert result is None
