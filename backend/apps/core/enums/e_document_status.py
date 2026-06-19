from django.db import models


class EDocumentStatus(models.TextChoices):
    UPLOADED = "uploaded", "Uploaded"
    PROCESSING = "processing", "Processing"
    INDEXED = "indexed", "Indexed"
    FAILED = "failed", "Failed"
