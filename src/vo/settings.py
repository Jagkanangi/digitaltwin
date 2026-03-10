from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class ConnectionConfig(BaseModel):
    db_host: str = "localhost"
    db_port: int = 8000
    db_type: str = "ChromaDB"
    redis_host: str = "localhost"
    redis_port: int = 6379

class DBRetrievalConfig(BaseModel):
    nn_count: int = 5

class ModelsConfig(BaseModel):
    chunking_model : str = "text-embedding-3-small"
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"

class LLMIntentProvider(BaseModel):
    host:str = "http://localhost:11434"
    provider : str = "ollama"
    model : str = "llama3"

class LLMSettingsConfig(BaseModel):
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    llm_rag_enabled: bool = True

class ChunkSettingsConfig(BaseModel):
    chunk_size: int = 500
    chunk_overlap: int = 50

class SystemSubConfig(BaseModel):
    allowed_origins: str = "*"
    env_name: str = "local"
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    llm_settings: LLMSettingsConfig = Field(default_factory=LLMSettingsConfig)
    llm_intent_provider: LLMIntentProvider = Field(default_factory=LLMIntentProvider)
    chunk_settings: ChunkSettingsConfig = Field(default_factory=ChunkSettingsConfig)

class PersonaSettingsConfig(BaseModel):
    persona_temp: float = 0.1
    code_explanation: float = 0.5
    tech_explanation: float = 0.5
    persona_collection_name : str = "jag_bio"
class FileLocations(BaseModel):
    document_to_process_dir: str = "data/input_rag"
    document_processed_dir: str = "data/rag_processed"
class UISettings(BaseModel):
    chat_service_url: str = "http://localhost:8000/chat"
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter='__',
        env_file=('.env', '.env.shared'),
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False
    )


    port: int = Field(default=8080, validation_alias='PORT')
    host: str ="0.0.0.0"
    chroma_server_auth_credentials : str = Field(default=..., min_length=1)
    redis_password : str = Field(default=..., min_length=1)
    connection: ConnectionConfig = Field(default_factory=ConnectionConfig)
    db_retrieval: DBRetrievalConfig = Field(default_factory=DBRetrievalConfig)
    system: SystemSubConfig = Field(default_factory=SystemSubConfig)
    persona_settings: PersonaSettingsConfig = Field(default_factory=PersonaSettingsConfig)
    ui_settings: UISettings = Field(default_factory=UISettings)
    file_locations : FileLocations = Field(default_factory=FileLocations)

settings = Settings()
