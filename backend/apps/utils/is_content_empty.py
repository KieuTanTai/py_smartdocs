from pathlib import Path

from sys_services.interfaces.i_logging import ILogger
from sys_services.logging import DEFAULT_LOGGER


def check_empty_content(
    content: str, call_by: str, logger: ILogger | None = None
) -> bool:
    logger = logger or DEFAULT_LOGGER
    if content.strip() == "":
        logger.warning(
            f"Content is empty for `{call_by}`. This may indicate an issue with the OCR extraction or normalization process.",
            source=Path(__file__).name,
        )
        return False
    logger.info(
        f"Content is not empty for '{call_by}'.",
        source=Path(__file__).name,
    )
    return True


def check_empty_contents(
    content: list[str], call_by: str, logger: ILogger | None = None
) -> bool:
    logger = logger or DEFAULT_LOGGER
    if all(item.strip() == "" for item in content):
        logger.warning(
            f"Content list is empty for `{call_by}`. This may indicate an issue with the OCR extraction or normalization process.",
            source=Path(__file__).name,
        )
        return False
    logger.info(
        f"Content list is not empty for `{call_by}`.",
        source=Path(__file__).name,
    )
    return True
