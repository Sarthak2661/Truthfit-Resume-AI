class ProviderError(RuntimeError):
    """Base class for provider failures that should fail an analysis run."""

    code = "provider_error"
    retryable = False

    def __init__(self, message: str, *, provider: str = "", model: str = ""):
        super().__init__(message)
        self.provider = provider
        self.model = model


class ProviderAuthenticationError(ProviderError):
    code = "provider_authentication_error"


class ProviderRateLimitError(ProviderError):
    code = "provider_rate_limit"
    retryable = True


class ProviderTimeoutError(ProviderError):
    code = "provider_timeout"
    retryable = True


class ProviderUnavailableError(ProviderError):
    code = "provider_unavailable"
    retryable = True


class ProviderModelUnavailableError(ProviderError):
    code = "provider_model_unavailable"


class ProviderResponseError(ProviderError):
    code = "provider_response_error"


def public_provider_message(error: ProviderError) -> str:
    messages = {
        ProviderAuthenticationError: "The provider rejected the API key. Check the key and try again.",
        ProviderRateLimitError: "The provider rate limit was reached. Wait briefly and retry the analysis.",
        ProviderTimeoutError: "The provider did not respond in time. Retry the analysis.",
        ProviderUnavailableError: "The provider is temporarily unavailable. Retry the analysis later.",
        ProviderModelUnavailableError: "The selected model is unavailable. Choose another listed model and retry.",
        ProviderResponseError: "The provider returned an invalid analysis response. Retry the analysis.",
    }
    return messages.get(type(error), "The provider could not complete this analysis.")
