try:
    import itsdangerous
    print("itsdangerous: OK")
except ImportError as e:
    print(f"itsdangerous: MISSING ({e})")

try:
    import authlib
    print("authlib: OK")
except ImportError as e:
    print(f"authlib: MISSING ({e})")

try:
    import reportlab
    print("reportlab: OK")
except ImportError as e:
    print(f"reportlab: MISSING ({e})")

import os
print(f"GOOGLE_CLIENT_ID: {'Set' if os.environ.get('GOOGLE_CLIENT_ID') else 'Missing'}")
print(f"GOOGLE_REDIRECT_URI: {os.environ.get('GOOGLE_REDIRECT_URI')}")
