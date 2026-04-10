

from app.core.security import create_access_token, decode_token

from app.core.config import settings

try:

    token = create_access_token("test-subject")

    print(f"Token: {token[:10]}...")

    decoded = decode_token(token)

    print(f"Decoded: {decoded}")

except Exception as e:

    print(f"Error: {e}")

