import re
from pathlib import Path

from sys_services.logging import Logger
from sys_services.enums.type_message import TypeMessage

def check_empty_content(content: str, call_by: str) -> bool:
    if content.strip() == "":
        Logger.log(
            TypeMessage.WARNING,
            f"Content is empty for `{call_by}`. This may indicate an issue with the OCR extraction or normalization process.",
            source_log=Path(__file__).name
        )
        return False
    Logger.log(
        TypeMessage.INFO,
        f"Content is not empty for `{call_by}`.",
        source_log=Path(__file__).name
    )
    return True


def check_empty_contents(content: list[str], call_by: str) -> bool:
    if all(item.strip() == "" for item in content):
        Logger.log(
            TypeMessage.WARNING,
            f"Content list is empty for `{call_by}`. This may indicate an issue with the OCR extraction or normalization process.",
            source_log=Path(__file__).name
        )
        return False
    Logger.log(
        TypeMessage.INFO,
        f"Content list is not empty for `{call_by}`.",
        source_log=Path(__file__).name
    )
    return True