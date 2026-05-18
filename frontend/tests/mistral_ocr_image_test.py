import base64
from pathlib import Path

from mistralai.client import Mistral
from sys_services.read_config.read_mistral_config import MISTRAL_CONFIG
from sys_services.logging import DEFAULT_LOGGER

ROOT_DIR = Path(__file__).resolve().parents[2]
IMAGE_PATH = ROOT_DIR / "docs" / "pdfs_test" / "1000125758-Picsart-AiImageEnhancer.jpg"

client = Mistral(api_key=MISTRAL_CONFIG["api_key"])
logger = DEFAULT_LOGGER


def encode_image(image_path: Path) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def test_image_ocr() -> None:
    base64_image = encode_image(IMAGE_PATH)
    data_url = f"data:image/jpeg;base64,{base64_image}"

    ocr_response = client.ocr.process(
        model=MISTRAL_CONFIG["ocr_model"],
        document={
            "type": "image_url",
            "image_url": data_url,
        },
        include_image_base64=True,
    )

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"image_output_{IMAGE_PATH.stem}.md"

    try:
        with open(output_path, "w") as output_file:
            for page in ocr_response.pages:
                output_file.write(page.markdown)
        logger.info(
            f"OCR image output written to: {output_path}",
            source=Path(__file__).name,
        )
    except Exception as exc:
        logger.error(
            f"Failed to write OCR image output: {exc}",
            source=Path(__file__).name,
        )


if __name__ == "__main__":
    test_image_ocr()
