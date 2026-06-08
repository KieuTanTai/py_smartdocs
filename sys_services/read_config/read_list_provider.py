#! NOTE: NEED TO FIX CALLING, THIS FILE MUST BE CALLED ONE TIME AND NOT CALL AGAIN

import os
import re
from typing import List
from dotenv import load_dotenv

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.system.i_provider import IProvider
from sys_services.system_dirs import ROOT_DIR

load_dotenv(ROOT_DIR / ".env")

def get_ai_providers_config() -> List[IProvider]:
    pattern_embedding = re.compile(r"^(?=.*EMBED).*MODEL$", re.IGNORECASE)
    pattern_model = re.compile(r"^(?!.*(?:EMBED|OCR)).*_MODEL$", re.IGNORECASE)
    pattern_provider = re.compile(r"^([A-Z0-9]+)_(?:.*_)?MODEL$", re.IGNORECASE)
    temp_data = {}
    keys = os.environ
    # 3. Duyệt qua os.environ để phân loại
    for key in keys:
        match_provider = pattern_provider.match(key)
        if not match_provider:
            continue

        match_model = pattern_model.match(key)
        match_embedding = pattern_embedding.match(key)
        name = None
        model_value = None
        embedding_value = None


        try: 
            name = EProviderName[match_provider.group(1)]
        except (KeyError, IndexError) as ex:
            continue

        if name not in temp_data:
            temp_data[name] = {"model_name": None, "embed_model_name": None}

        if match_model:
            model_value = os.getenv(key)
            temp_data[name]["model_name"] = model_value

        elif match_embedding:
            embedding_value = os.getenv(key)
            temp_data[name]["embed_model_name"] = embedding_value

    return __mapping_results(temp_data)

def __mapping_results(temp_data: dict) -> List[IProvider]:
    providers = list[IProvider]()
    for name, data in temp_data.items():
        if data["model_name"] is not None and data["embed_model_name"] is not None:
            provider = IProvider(
                provider_name=name,
                model_name=data["model_name"],
                embed_model_name=data["embed_model_name"],
            )
            providers.append(provider)
    return providers

LIST_PROVIDERS = get_ai_providers_config()
LIST_MODELS = [provider.model_name for provider in LIST_PROVIDERS if provider is not None]
LIST_EMBEDDING_MODELS = [provider.embed_model_name for provider in LIST_PROVIDERS if provider is not None]
print("Loaded providers:", LIST_PROVIDERS)
print("Loaded models:", LIST_MODELS)
print("Loaded embedding models:", LIST_EMBEDDING_MODELS)
