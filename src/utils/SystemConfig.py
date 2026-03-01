
import yaml
import os
import re
from threading import Lock
import logging
from src.vo.Config import SystemConfigModel

logger = logging.getLogger(__name__)


class _SystemConfig:
    """
    A singleton class to manage system configuration from a YAML file.
    It handles environment variable substitution and validation using Pydantic.
    """
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        with self._lock:
            if hasattr(self, '_initialized'):
                return
            self._initialized = True
            
            # This path is relative to the project root.
            config_path = "src/config/system_config.yaml"
            with open(config_path, "r") as f:
                raw_config_content = f.read()

            def env_var_replacer(match):
                var_name, default_value = match.groups()
                return os.getenv(var_name, default_value)

            # Expanded variables with defaults, e.g., ${VAR:-default}
            expanded_config = re.sub(r'\$\{([^:}]+):-([^}]+)\}', env_var_replacer, raw_config_content)
            # Expanded simple variables, e.g., ${VAR}
            expanded_config = os.path.expandvars(expanded_config)
            
            raw_config = yaml.safe_load(expanded_config)
            self.config = SystemConfigModel(**raw_config)

config = _SystemConfig().config