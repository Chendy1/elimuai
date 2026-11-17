import pytest

from app.core.passwords import validate_password_strength
from app.core.rate_limit import RateLimiter
from app.core.security import hash_password, hash_token, new_token, verify_password


def test_hash_roundtrip_and_salting():
    h1, h2 = hash_password("a-good-passphrase"), hash_password("a-good-passphrase")
    assert h1.startswith("$argon2id$")
    assert h1 != h2
    assert verify_password(h1, "a-good-passphrase")
    assert not verify_password(h1, "wrong")
    assert not verify_password("not-a-hash", "anything")


def test_tokens_are_unique_and_hashed_deterministically():
    assert new_token() != new_token()
    assert hash_token("abc") == hash_token("abc")
    assert len(hash_token("abc")) == 64


@pytest.mark.parametrize("pw", ["short", "password123", "aaaaaaaaaaaa", "x" * 129])
def test_weak_passwords_rejected(pw):
    with pytest.raises(ValueError):
        validate_password_strength(pw)


def test_password_equal_to_email_rejected():
    with pytest.raises(ValueError):
        validate_password_strength("guardian@example.com", "Guardian@Example.com")


def test_good_password_accepted():
    assert validate_password_strength("correct-horse-battery") == "correct-horse-battery"


def test_rate_limiter_blocks_then_allows_after_reset():
    rl = RateLimiter()
    assert rl.check("k", 2, 60) is None
    assert rl.check("k", 2, 60) is None
    assert rl.check("k", 2, 60) is not None
    assert rl.check("other", 2, 60) is None
    rl.reset()
    assert rl.check("k", 2, 60) is None
