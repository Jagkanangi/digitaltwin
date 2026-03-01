from pydantic import BaseModel, Field

class ConnectionConfig(BaseModel):
    db_host: str = Field(..., alias='DB_HOST')
    db_port: int = Field(..., alias='DB_PORT')
    db_type: str = Field(..., alias='DB_TYPE')

class DBRetrievalConfig(BaseModel):
    nn_count: int = Field(..., alias='NN_COUNT')

class FileLocationsConfig(BaseModel):
    data_dir_name: str = Field(..., alias='DATA_DIR_NAME')
    document_to_process_dir: str = Field(..., alias='DOCUMENT_TO_PROCESS_DIR')
    document_processed_dir: str = Field(..., alias='DOCUMENT_PROCESSED_DIR')

class ModelsConfig(BaseModel):
    embedding_model: str = Field(..., alias='EMBEDDING_MODEL')
    llm_model: str = Field(..., alias='LLM_MODEL')
class LLM_INTENT_PROVIDER(BaseModel):
    host:str = Field(..., alias='HOST')
    provider : str = Field(..., alias='PROVIDER')
    model : str = Field(..., alias='MODEL')
class LLMSettingsConfig(BaseModel):
    llm_temperature: float = Field(..., alias='LLM_TEMPERATURE')
    llm_max_tokens: int = Field(..., alias='LLM_MAX_TOKENS')
    llm_rag_enabled: bool = Field(..., alias='LLM_RAG_ENABLED')

class ChunkSettingsConfig(BaseModel):
    chunk_size: int = Field(..., alias='CHUNK_SIZE')
    chunk_overlap: int = Field(..., alias='CHUNK_OVERLAP')

class SystemSubConfig(BaseModel):
    file_locations: FileLocationsConfig = Field(..., alias='FILE_LOCATIONS')
    models: ModelsConfig = Field(..., alias='MODELS')
    llm_settings: LLMSettingsConfig = Field(..., alias='LLM_SETTINGS')
    llm_intent_provider: LLM_INTENT_PROVIDER = Field(..., alias='LLM_INTENT_PROVIDER')
    chunk_settings: ChunkSettingsConfig = Field(..., alias='CHUNK_SETTINGS')

class PersonaSettingsConfig(BaseModel):
    persona_temp: float = Field(..., alias='PERSONA_TEMP')
    code_explanation: float = Field(..., alias='CODE_EXPLANATION')
    tech_explanation: float = Field(..., alias='TECH_EXPLANATION')
    persona_collection_name : str = Field(..., alias="PERSONA_COLLECTION_NAME")
class SystemConfigModel(BaseModel):
    connection: ConnectionConfig = Field(..., alias='Connection')
    db_retrieval: DBRetrievalConfig = Field(..., alias='DB_RETRIEVAL')
    system: SystemSubConfig = Field(..., alias='SYSTEM')
    persona_settings: PersonaSettingsConfig = Field(..., alias='PERSONA_SETTINGS')
