
import re

from backend.apps.core.interfaces.core.normalize.i_normalize import INormalize
from backend.apps.core.interfaces.system.i_logging import ILogger
from sys_services.logging import DEFAULT_LOGGER

class Normalize(INormalize):

    def __init__(self, looger = ILogger | None):
        self.logger = looger or DEFAULT_LOGGER

    def normalize(self, content: str) -> str:
        normalized_content = content.strip()
        normalized_content = re.sub(r'\n+', '\n', normalized_content)
        normalized_content = re.sub(r'[ \t]+', ' ', normalized_content)
        return normalized_content