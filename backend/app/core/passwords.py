"""Password policy (pure functions, no dependencies)."""

MIN_LENGTH = 10
MAX_LENGTH = 128

_COMMON = {
    "password", "password1", "password12", "password123", "1234567890", "12345678910",
    "qwertyuiop", "iloveyou123", "letmein1234", "welcome1234", "kenya12345", "elimuai123",
}


def validate_password_strength(password: str, email: str | None = None) -> str:
    """Return the password if acceptable, else raise ValueError with a learner-friendly message."""
    if not (MIN_LENGTH <= len(password) <= MAX_LENGTH):
        raise ValueError(f"Password must be {MIN_LENGTH} to {MAX_LENGTH} characters long.")
    if password.lower() in _COMMON or len(set(password)) < 4:
        raise ValueError("That password is too easy to guess. Please choose another.")
    if email and password.lower() == email.strip().lower():
        raise ValueError("Password must not be the same as your email address.")
    return password
