import os
import logging.config
import yaml
from pathlib import Path

def init():
    # 1. Define Paths relative to this file
    CURRENT_DIR = Path(__file__).parent
    SRC_DIR = CURRENT_DIR.parent
    PROJECT_ROOT = SRC_DIR.parent # This is /app in Docker

    # 2. Setup Log File Path
    log_file_path_env = os.getenv('LOG_FILE_PATH')
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

    if log_file_path_env:
        log_file_path = Path(log_file_path_env)
    else:
        # Use PROJECT_ROOT so logs are at the top level
        log_dir = PROJECT_ROOT / 'logs'
        log_dir.mkdir(exist_ok=True)
        log_file_path = log_dir / 'chattwin.log'

    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # 3. Locate and load YAML Config (Inside src/config)
    config_path = SRC_DIR / 'config' / 'logger.yaml'
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # 4. Set log file path and level in the config
    config['handlers']['fileHandler']['filename'] = str(log_file_path)
    config['loggers']['chattwin']['level'] = log_level
    config['root']['level'] = 'INFO'

    # 5. Initialize
    logging.config.dictConfig(config)