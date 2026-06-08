"""
Authentication module.
Implements JWT-based authentication with access/refresh tokens.
"""
from __future__ import annotations

import hashlib
import os
import time
import json
from functools import wraps

import jwt
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

# ── Token configuration ──────────────────────────────────────────────────────

_JWT_SECRET = os.getenv("JWT_SECRET", settings.SECRET_KEY)
_JWT_ALGORITHM = "HS256"
_ACCESS_TOKEN_TTL_SECONDS = 60 * 60       # 1 hour
_REFRESH_TOKEN_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days

_USERS_FILE = os.path.join(os.path.dirname(__file__), ".users.json")


# ── User store (file-based for demo; swap for DB in production) ─────────────

def _load_users() -> dict:
    try:
        with open(_USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_users(users: dict) -> None:
    with open(_USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ── Token helpers ───────────────────────────────────────────────────────────

def _make_access_token(email: str, name: str) -> str:
    payload = {
        "sub": email,
        "name": name,
        "type": "access",
        "exp": int(time.time()) + _ACCESS_TOKEN_TTL_SECONDS,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGORITHM)


def _make_refresh_token(email: str) -> str:
    payload = {
        "sub": email,
        "type": "refresh",
        "exp": int(time.time()) + _REFRESH_TOKEN_TTL_SECONDS,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGORITHM)


def _decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def _get_token_from_request(request) -> str | None:
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


# ── Auth decorator for protected views ──────────────────────────────────────

def require_auth(view_func):
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        token = _get_token_from_request(request)
        if not token:
            return Response(
                {"error": "Authorization header missing or malformed."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        payload = _decode_token(token)
        if not payload:
            return Response(
                {"error": "Token missing, expired, or invalid."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if payload.get("type") != "access":
            return Response(
                {"error": "Invalid token type."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        request.auth_email = payload.get("sub")
        request.auth_name = payload.get("name")
        return view_func(self, request, *args, **kwargs)
    return wrapper


# ── Views ────────────────────────────────────────────────────────────────────

class SignupView(APIView):
    """
    POST /api/auth/signup/
    Body: { "email": "...", "password": "...", "name": "..." }
    Returns: { "access_token", "refresh_token", "user": { id, email, name } }
    """

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password") or ""
        name = (request.data.get("name") or "").strip()

        if not email or "@" not in email:
            return Response({"error": "A valid email is required."}, status=status.HTTP_400_BAD_REQUEST)
        if len(password) < 6:
            return Response({"error": "Password must be at least 6 characters."}, status=status.HTTP_400_BAD_REQUEST)
        if not name:
            return Response({"error": "Name is required."}, status=status.HTTP_400_BAD_REQUEST)

        users = _load_users()

        if email in users:
            return Response({"error": "An account with this email already exists."}, status=status.HTTP_409_CONFLICT)

        users[email] = {
            "name": name,
            "password_hash": _hash_password(password),
        }
        _save_users(users)

        access_token = _make_access_token(email, name)
        refresh_token = _make_refresh_token(email)

        return Response({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {"id": email, "email": email, "name": name},
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    POST /api/auth/login/
    Body: { "email": "...", "password": "..." }
    Returns: { "access_token", "refresh_token", "user": { id, email, name } }
    """

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password") or ""

        if not email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        users = _load_users()
        user = users.get(email)

        if not user or user["password_hash"] != _hash_password(password):
            return Response({"error": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = _make_access_token(email, user["name"])
        refresh_token = _make_refresh_token(email)

        return Response({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {"id": email, "email": email, "name": user["name"]},
        }, status=status.HTTP_200_OK)


class RefreshTokenView(APIView):
    """
    POST /api/auth/refresh/
    Body: { "refresh_token": "..." }
    Returns: { "access_token", "refresh_token" }
    """

    def post(self, request):
        refresh_token = request.data.get("refresh_token") or ""
        payload = _decode_token(refresh_token)

        if not payload or payload.get("type") != "refresh":
            return Response({"error": "Invalid or expired refresh token."}, status=status.HTTP_401_UNAUTHORIZED)

        email = payload.get("sub")
        users = _load_users()
        user = users.get(email)
        if not user:
            return Response({"error": "User not found."}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = _make_access_token(email, user["name"])
        new_refresh_token = _make_refresh_token(email)

        return Response({
            "access_token": access_token,
            "refresh_token": new_refresh_token,
        }, status=status.HTTP_200_OK)


class MeView(APIView):
    """
    GET /api/auth/me/
    Returns: { "id", "email", "name" } of the authenticated user.
    """

    @require_auth
    def get(self, request):
        return Response({
            "id": request.auth_email,
            "email": request.auth_email,
            "name": request.auth_name,
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    (Client-side: discard tokens; no server-side token blocklist for simplicity.)
    """

    def post(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)
