from dataclasses import dataclass, field
from typing import Dict
from threading import Lock
from desktop_app.common.logger import logger


@dataclass
class SettingsProxy:
    settings: Dict = field(default_factory=dict)
    lock: Lock = Lock()

    def get(self, key: str):
        with self.lock:
            try:
                return self.settings[key]
            except Exception as e:
                logger.error("[Settings Proxy] Failed to get key, doesn't exist. KEY: " + key)

    def set(self, key: str, value):
        with self.lock:
            self.settings[key] = value

    def get_settings(self) -> Dict:
        return self.settings

    def load(self, settings) -> None:
        with self.lock:
            for key, value in settings.items():
                self.settings[key] = value

    def show(self):
        with self.lock:
            print(self.settings)