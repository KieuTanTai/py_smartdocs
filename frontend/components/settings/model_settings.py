from typing import List

from shiny import ui
from backend.apps.core.interfaces.dataclass.system.i_provider import IProvider

#* NOTE: using list[IProvider] instead of list[str] because we need to get the model name and provider name to display in the UI, and also to send the request to the backend when create conversation, if we only use list[str], 
#* we will lose the provider name information, and we need to do extra work to get the provider name from the model name, which is not efficient and also not necessary because we can get the provider name directly from the IProvider object. So using list[IProvider] is more convenient and efficient in this case.
def model_settings_ui(object_providers: list[IProvider]) -> ui.Tag:
    mode_choices = ["normal", "graph"]

    return ui.tags.div(
        ui.tags.div(
            ui.tags.div(
                ui.input_select(
                    "mode_select",
                    "Mode",
                    choices={c: c for c in mode_choices},
                    selected="normal",
                ),
                class_="button-select-wrap",
            ),
            class_="select-pill",
        ),
        ui.tags.div(
            ui.tags.div(
                ui.input_select(
                    "model_select",
                    "Model",
                    choices={object_provider.provider_name.value: object_provider.model_name for object_provider in object_providers},
                    selected=object_providers[0].model_name if object_providers else "auto",
                ),
                class_="button-select-wrap",
            ),
            class_="select-pill",
        ),
        class_="model-settings",
    )
