import json
import os

class ConfigReader:
    def __init__(self, config_path: str):
        """
        Initializes the ConfigReader.
        :param config_path: Path to JSON config file.
        """
        self.config_path = config_path
        self._config_data = {}
        self.load_config()

    def load_config(self):
        """Loads the JSON config from the file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config_data = json.load(f)

    def get(self, key: str, default=None):
        """
        Retrieves a value from the config using dot notation for nested keys.
        Example: "database.host"
        """
        keys = key.split(".")
        data = self._config_data
        for k in keys:
            if isinstance(data, dict) and k in data:
                data = data[k]
            else:
                return default
        return data

    def get_bool(self, key: str, default=False) -> bool:
        """Returns a boolean value from the config."""
        val = self.get(key, default)
        return bool(val) if isinstance(val, (bool, int, str)) else default

    def get_object(self, key: str, default=None):
        """Returns nested objects (dicts) from the config."""
        val = self.get(key, default)
        if isinstance(val, dict):
            # Optional: return a new ConfigReader for nested object
            nested = ConfigReader.__new__(ConfigReader)  # bypass __init__
            nested._config_data = val
            nested.config_path = None
            return nested
        return val

    def all(self):
        """Returns the whole config dictionary."""
        return self._config_data

    def reload(self):
        """Reloads the config from file."""
        self.load_config()
  
    def getIndicatorsConfig(self):
        return self._config_data['Indicators'] if 'Indicators' in self._config_data else []
    
    def getStructuresConfig(self):
        return self._config_data['Structures'] if 'Structures' in self._config_data else []
    
    def getModifiersConfig(self):
        return self._config_data['Modifiers'] if 'Modifiers' in self._config_data else []
    
    def getRollingRegression(self):
        return self._config_data['RollingRegression'] if 'RollingRegression' in self._config_data else None