from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_hash_password_does_not_store_plaintext():
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"


def test_verify_password_roundtrip():
    hashed = hash_password("s3cret!")
    assert verify_password("s3cret!", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_access_token_roundtrip_carries_subject_and_role():
    token = create_access_token(subject="user@example.com", role="admin")
    payload = decode_access_token(token)
    assert payload["sub"] == "user@example.com"
    assert payload["role"] == "admin"


def test_decode_access_token_rejects_garbage():
    assert decode_access_token("not-a-real-token") is None
