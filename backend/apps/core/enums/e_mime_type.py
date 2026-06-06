from enum import Enum


class EMimeType(str, Enum):
    PDF = "application/pdf"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    TXT = "text/plain"
    JPEG = "image/jpeg"
    PNG = "image/png"
    JPG = "image/jpg"
    TIFF = "image/tiff"
