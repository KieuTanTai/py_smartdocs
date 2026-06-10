class ISmartdocsException(Exception):
    """
    Base exception for all SmartDocs application errors.
    """
    def __init__(self, message: str, error_code: str | None = None):
        super().__init__(message)
        self.error_code = error_code
        super().__init__(message)