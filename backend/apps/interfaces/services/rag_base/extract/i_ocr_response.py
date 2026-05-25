from mistralai.client.models import OCRResponse


# DEPRECATED: This interface is deprecated and will be removed in future versions. Please use the ICompletionResponse interface instead for OCR responses.
class IOCRResponse(OCRResponse):
    """
    Interface for OCR response.
    Extends OCRResponse with additional fields if needed.
    """

    pass
