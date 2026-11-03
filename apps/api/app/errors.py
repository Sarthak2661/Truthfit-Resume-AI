class ResourceNotFoundError(Exception):
    pass


class UploadTooLargeError(ValueError):
    pass


class AnalysisQuotaExceededError(Exception):
    def __init__(self, limit: int, used: int, retry_after_seconds: int):
        super().__init__("Daily analysis limit reached. Try again tomorrow.")
        self.limit = limit
        self.used = used
        self.retry_after_seconds = retry_after_seconds
