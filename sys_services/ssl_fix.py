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
