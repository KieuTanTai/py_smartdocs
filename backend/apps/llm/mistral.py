import os

# Fix SSL certificate verification on Windows / environments with missing root CAs.
# MUST be called BEFORE any httpx / httpcore / google-genai imports.
_SSL_FIX_APPLIED = False


def apply_ssl_fix() -> None:
    """Patch ssl.create_default_context to use certifi CA bundle.
    This ensures all HTTPS connections (via httpx, httpcore, requests, urllib)
    use the correct root certificates, even when the system store is incomplete.
    """
    global _SSL_FIX_APPLIED
    if _SSL_FIX_APPLIED:
        return
    _SSL_FIX_APPLIED = True

    try:
        import ssl as _ssl
        import certifi as _certifi

        _ca_bundle = _certifi.where()
        os.environ.setdefault("SSL_CERT_FILE", _ca_bundle)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", _ca_bundle)
        os.environ.setdefault("CURL_CA_BUNDLE", _ca_bundle)

        _orig_cdc = _ssl.create_default_context

        def _patched_cdc(
            purpose=_ssl.Purpose.SERVER_AUTH,
            *,
            cafile=None,
            capath=None,
            cadata=None,
        ):
            ctx = _orig_cdc(purpose=purpose, cafile=None, capath=capath, cadata=cadata)
            ctx.load_verify_locations(cafile=_ca_bundle)
            return ctx

        _ssl.create_default_context = _patched_cdc

        # Also patch ssl.wrap_socket for older code paths
        _orig_ws = _ssl.wrap_socket

        def _patched_ws(
            sock, keyfile=None, certfile=None, server_side=False,
            cert_reqs=_ssl.CERT_REQUIRED, ssl_version=None, ciphers=None,
        ):
            return _orig_ws(
                sock, keyfile=keyfile, certfile=certfile,
                server_side=server_side, cert_reqs=cert_reqs,
                ssl_version=ssl_version, ciphers=ciphers,
            )

        _ssl.wrap_socket = _patched_ws

    except Exception:
        pass  # certifi not available or patching failed; fallback to system defaults


apply_ssl_fix()

import ssl
import httpx
import numpy as np
from mistralai.client import Mistral
from backend.apps.core.interfaces.core.i_dataclass_transaction import (
    ICompletionRequest,
    IEmbeddingResponse,
)
from backend.apps.core.interfaces.llm.i_llm_client import ILLMClient
from backend.apps.core.interfaces.system.i_logging import ILogger


def _build_ssl_context() -> ssl.SSLContext:
    """Build SSL context using certifi CA bundle (explicit fallback)."""
    try:
        import certifi as _certifi
    except ImportError:
        return ssl.create_default_context()

    ctx = ssl.create_default_context()
    ctx.load_verify_locations(cafile=_certifi.where())
    return ctx


def _build_httpx_client(timeout: float) -> httpx.Client:
    """Build httpx client with proper SSL certificate verification."""
    return httpx.Client(timeout=timeout, verify=_build_ssl_context())


class MistralClient(ILLMClient):

    def __init__(
        self,
        api_key: str,
        logger: ILogger,
        timeout: float = 60.0,
    ):
        if (api_key is None) or (api_key.strip() == ""):
            raise ValueError("API key must be provided for MistralClient.")
        self.timeout = timeout
        self.logger = logger
        http_client = _build_httpx_client(timeout)
        self.client = Mistral(api_key=api_key, client=http_client)

    def generate(self, request: ICompletionRequest) -> str:
        self.logger.info("Sending request to Mistral API.", source=str(self.__class__))
        response = self.client.chat.complete(
            model=request.model,
            messages=[{"role": "user", "content": request.prompt}]
        )
        if response.choices[0].message is None:
            self.logger.error("Response from Mistral API does not contain message.", source=str(self.__class__))
            raise ValueError("Response from Mistral API does not contain message.")
        self.logger.info("successfully generated content using Mistral API.", source=str(self.__class__))
        return str(response.choices[0].message.content)

    def embedding(self, request: ICompletionRequest) -> IEmbeddingResponse:
        self.logger.info(
            "Generating embedding from Mistral API.", source=str(self.__class__)
        )
        response = self.client.embeddings.create(
            model=request.model,
            inputs=[request.prompt],
        )
        if not response.data:
            self.logger.error("Response from Mistral API does not contain data.", source=str(self.__class__))
            raise ValueError("Response from Mistral API does not contain data.")
        self.logger.info("successfully generated embedding using Mistral API.", source=str(self.__class__))
        values = response.data[0].embedding
        if values is None:
            self.logger.error("Embedding response from Mistral API does not contain values.", source=str(self.__class__))
            raise ValueError("Embedding response from Mistral API does not contain values.")
        return IEmbeddingResponse(embedding=np.array(values), dimensions=len(values), shape=(len(values),))

    def is_available(self, model: str) -> bool:
        self.logger.info(
            "Checking Mistral API availability.", source=str(self.__class__)
        )
        try:
            response = self.client.chat.complete(
                model=model,
                messages=[{"role": "user", "content": "Hello"}]
            )
            return response.choices[0].message is not None
        except Exception as e:
            self.logger.error(
                f"Mistral API is not available: {str(e)}", source=str(self.__class__)
            )
            return False
