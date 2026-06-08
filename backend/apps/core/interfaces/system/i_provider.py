from dataclasses import dataclass
from backend.apps.core.enums.e_provider_name import EProviderName


@dataclass
class IProvider:
    provider_name: EProviderName
    model_name: str
    embed_model_name: str