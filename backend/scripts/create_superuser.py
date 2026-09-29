"""
Create (or promote) a superuser interactively:

    python -m scripts.create_superuser                # uses SUPERUSER_USERNAME (default harak1r1)
    python -m scripts.create_superuser --username bob
"""

import argparse
import getpass

from sqlalchemy import select

from app.bootstrap import create_user
from app.config import get_settings
from app.database import SessionLocal, init_db
from app.models import User
from app.security import hash_password


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default=get_settings().superuser_username)
    args = parser.parse_args()

    password = getpass.getpass(f"Password for '{args.username}': ")
    if len(password) < 8:
        raise SystemExit("Password must be at least 8 characters")
    if password != getpass.getpass("Repeat password: "):
        raise SystemExit("Passwords do not match")

    init_db()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == args.username))
        if user:
            user.password_hash = hash_password(password)
            user.is_superuser = True
            user.is_active = True
            db.commit()
            print(f"Updated existing user '{args.username}' -> superuser")
        else:
            create_user(db, args.username, password, is_superuser=True)
            print(f"Superuser '{args.username}' created")


if __name__ == "__main__":
    main()
