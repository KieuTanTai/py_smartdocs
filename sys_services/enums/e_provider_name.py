from enum import Enum

class EProviderName(str, Enum):
    MISTRAL = "mistral"
    GEMINI = "gemini"
    OLLAMA = "ollama"