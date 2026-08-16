import uuid

from app.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_roundtrip():
    hashed = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_password_hashes_are_salted():
    h1 = hash_password("same-password")
    h2 = hash_password("same-password")
    assert h1 != h2


def test_access_token_roundtrip():
    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    decoded = decode_access_token(token)
    assert decoded == user_id


def test_access_token_rejects_garbage():
    assert decode_access_token("not-a-real-token") is None
