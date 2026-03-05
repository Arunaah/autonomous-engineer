import os

class Config:
    def __init__(self):
        self.base_url = None
        self.api_key = None

    def load_config(self, config_path):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found at {config_path}")

        with open(config_path, 'r') as file:
            for line in file:
                if line.startswith('BASE_URL'):
                    self.base_url = line.split('=')[1].strip()
                elif line.startswith('API_KEY'):
                    self.api_key = line.split('=')[1].strip()

    def get_base_url(self):
        if self.base_url is None:
            raise ValueError("Base URL has not been set")
        return self.base_url

    def get_api_key(self):
        if self.api_key is None:
            raise ValueError("API Key has not been set")
        return self.api_key