import os
import json
from pathlib import Path

class Config:
    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser("~"), ".luna-ai")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.default_config = {
            "model_path": "",
            "model_config": {
                "n_ctx": 2048,
                "n_threads": 4,
                "n_gpu_layers": 0
            }
        }
        self.ensure_config_exists()
        self.load_config()

    def ensure_config_exists(self):
        """Create config directory and file if they don't exist"""
        os.makedirs(self.config_dir, exist_ok=True)
        if not os.path.exists(self.config_file):
            with open(self.config_file, 'w') as f:
                json.dump(self.default_config, f, indent=4)

    def load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = self.default_config

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_model_path(self):
        """Get the configured model path"""
        return self.config.get("model_path", "")

    def set_model_path(self, path):
        """Set the model path in configuration"""
        self.config["model_path"] = path
        self.save_config()

    def get_model_config(self):
        """Get the model configuration"""
        return self.config.get("model_config", self.default_config["model_config"])

    def set_model_config(self, config):
        """Set the model configuration"""
        self.config["model_config"] = config
        self.save_config()

config = Config() 