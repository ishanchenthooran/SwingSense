"""
Tests for JWKS-based JWT verification in app.core.auth.

These tests never hit Supabase's network JWKS endpoint. Instead they spin up a
local EC keypair, sign tokens with it, and monkeypatch PyJWKClient.fetch_data
(the one method that performs the HTTP request) to return a JWKS built from
the local public key. Everything else -- kid matching, signature verification,
expiry checks, the ES256/RS256 allow-list -- runs through the real PyJWT /
PyJWKClient code paths exercised by app.core.auth.
"""
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jwt import PyJWKClient
from jwt.algorithms import ECAlgorithm

from app.core import auth

KID = "test-kid-1"


@pytest.fixture
def keypair():
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    return private_key, public_key


@pytest.fixture
def jwks_client(monkeypatch, keypair):
    """A real PyJWKClient wired to a local JWKS instead of the network."""
    _private_key, public_key = keypair
    jwk_dict = ECAlgorithm(ECAlgorithm.SHA256).to_jwk(public_key, as_dict=True)
    jwk_dict.update(kid=KID, use="sig", alg="ES256")
    jwks_document = {"keys": [jwk_dict]}

    client = PyJWKClient(uri="https://example.invalid/jwks.json", cache_keys=True)
    monkeypatch.setattr(client, "fetch_data", lambda: jwks_document)
    monkeypatch.setattr(auth, "_jwk_client", client)
    return client


def make_token(private_key, claims, kid=KID, algorithm="ES256"):
    headers = {"kid": kid} if kid is not None else {}
    return jwt.encode(claims, private_key, algorithm=algorithm, headers=headers)


def credentials_for(token):
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_valid_token_accepted(jwks_client, keypair):
    private_key, _ = keypair
    token = make_token(
        private_key,
        {"sub": "user-123", "email": "golfer@example.com", "exp": int(time.time()) + 3600},
    )

    result = auth.get_current_user(credentials_for(token))

    assert result == {"user_id": "user-123", "email": "golfer@example.com"}


def test_expired_token_rejected(jwks_client, keypair):
    private_key, _ = keypair
    token = make_token(
        private_key,
        {"sub": "user-123", "email": "golfer@example.com", "exp": int(time.time()) - 60},
    )

    with pytest.raises(HTTPException) as exc_info:
        auth.get_current_user(credentials_for(token))

    assert exc_info.value.status_code == 401


def test_tampered_signature_rejected(jwks_client, keypair):
    private_key, _ = keypair
    token = make_token(
        private_key,
        {"sub": "user-123", "email": "golfer@example.com", "exp": int(time.time()) + 3600},
    )
    header_b64, payload_b64, signature_b64 = token.split(".")
    # Flip a character in the middle of the signature (not the last char --
    # trailing base64url chars can carry discarded padding bits that don't
    # affect the decoded bytes) to invalidate it while staying valid base64url.
    idx = len(signature_b64) // 2
    flipped_char = "A" if signature_b64[idx] != "A" else "B"
    tampered_signature = signature_b64[:idx] + flipped_char + signature_b64[idx + 1:]
    tampered_token = f"{header_b64}.{payload_b64}.{tampered_signature}"

    with pytest.raises(HTTPException) as exc_info:
        auth.get_current_user(credentials_for(tampered_token))

    assert exc_info.value.status_code == 401


def test_missing_kid_handled_gracefully(jwks_client, keypair):
    private_key, _ = keypair
    token = make_token(
        private_key,
        {"sub": "user-123", "email": "golfer@example.com", "exp": int(time.time()) + 3600},
        kid=None,
    )

    with pytest.raises(HTTPException) as exc_info:
        auth.get_current_user(credentials_for(token))

    assert exc_info.value.status_code == 401
