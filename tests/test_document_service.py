import pytest
import os
from unittest.mock import patch, MagicMock
from src.services.DocumentService import DocumentService

@pytest.fixture
def mock_config():
    with patch("src.services.DocumentService.config") as mock:
        mock.system.file_locations.document_to_process_dir = "input"
        mock.system.file_locations.document_processed_dir = "processed"
        yield mock

@patch("os.makedirs")
@patch("os.listdir")
@patch("os.path.isfile")
@patch("os.rename")
def test_process_and_embed_directory(mock_rename, mock_isfile, mock_listdir, mock_makedirs, mock_config):
    mock_listdir.return_value = ["file1.txt", "file2.txt"]
    mock_isfile.return_value = True
    
    mock_embedding_model_class = MagicMock()
    mock_vector_db_service = MagicMock()
    
    service = DocumentService(mock_embedding_model_class, mock_vector_db_service)
    
    # Mock _process_and_embed_file to avoid deep nesting in this test
    with patch.object(DocumentService, "_process_and_embed_file") as mock_process_file:
        service.process_and_embed_directory("test_bucket")
        
        assert mock_makedirs.call_count == 2
        assert mock_process_file.call_count == 2
        assert mock_rename.call_count == 2
        mock_rename.assert_any_call("input/file1.txt", "processed/file1.txt")

def test_process_and_embed_file_logic():
    mock_embedding_model_class = MagicMock()
    mock_vector_db_service = MagicMock()
    
    # Setup mock embedding model return value
    mock_model_instance = MagicMock()
    mock_embedding_model_class.return_value = mock_model_instance
    
    mock_chunk1 = MagicMock()
    mock_chunk1.text = "chunk 1"
    mock_chunk1.embedding = [0.1, 0.2]
    
    mock_chunk2 = MagicMock()
    mock_chunk2.text = "chunk 2"
    mock_chunk2.embedding = [0.3, 0.4]
    
    mock_doc = MagicMock()
    mock_doc.chunks = [mock_chunk1, mock_chunk2]
    mock_doc.metadata = {"source": "test.txt"}
    
    mock_model_instance.get_embeddings.return_value = [mock_doc]
    
    # Mock vector db wrapper
    mock_wrapper = MagicMock()
    mock_vector_db_service.get_db_wrapper.return_value = mock_wrapper
    
    service = DocumentService(mock_embedding_model_class, mock_vector_db_service)
    service._process_and_embed_file("test.txt", "test_bucket")
    
    mock_embedding_model_class.assert_called_once_with(file_name="test.txt", directory_name=None, text_to_chunk=None)
    mock_wrapper.add.assert_called_once()
    args, kwargs = mock_wrapper.add.call_args
    assert kwargs["texts"] == ["chunk 1", "chunk 2"]
    assert kwargs["embeddings"] == [[0.1, 0.2], [0.3, 0.4]]
    assert len(kwargs["metadatas"]) == 2
