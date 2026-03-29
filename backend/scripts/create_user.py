#!/usr/bin/env python3
"""
CLI script to create the initial admin user.
Run once after first deployment:
    python scripts/create_user.py --username admin --password "YourSecurePassword"
"""
import argparse
import asyncio
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password


async def create_user(username: str, password: str) -> None:
    if len(password) < 8:
        print("Error: password must be at least 8 characters", file=sys.stderr)
        sys.exit(1)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == username.lower()))
        if result.scalar_one_or_none():
            print(f"Error: user '{username}' already exists", file=sys.stderr)
            sys.exit(1)

        user = User(username=username.lower(), hashed_password=hash_password(password))
        db.add(user)
        await db.commit()
        print(f"✓ User '{username}' created successfully (id={user.id})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create MediaTracker admin user")
    parser.add_argument("--username", required=True, help="Username (alphanumeric, max 50 chars)")
    parser.add_argument("--password", required=True, help="Password (min 8 chars)")
    args = parser.parse_args()
    asyncio.run(create_user(args.username, args.password))
