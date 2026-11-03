import re
import secrets
import string


def slug_base(name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return normalized[:90] if normalized else "agent"


def generate_slug(name: str) -> str:
    alphabet = string.ascii_lowercase + string.digits
    suffix = "".join(secrets.choice(alphabet) for _ in range(6))
    return f"{slug_base(name)}-{suffix}"
