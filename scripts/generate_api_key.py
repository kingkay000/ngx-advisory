import argparse
import hashlib
import os
import secrets
import sys

from sqlalchemy import create_engine, text

def generate_key(owner_name: str) -> None:
    # Looks for host level env overrides first, defaults cleanly to volume mount space
    db_url = os.getenv("NGX_DB_URL", "sqlite:////app/data/ngx_advisory.db")
    
    # Generate a cryptographically secure 32-byte tracking string
    raw_key  = "ngx_" + secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    engine = create_engine(db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {})
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO ngx_api_keys (key_hash, owner_name) VALUES (:h, :o)"),
            {"h": key_hash, "o": owner_name}
        )
        conn.commit()

    print(f"\n✅ API key generated for: {owner_name}")
    print(f"\n   Key — share this with the consumer, store it nowhere else:\n")
    print(f"    {raw_key}\n")
    print(f"   Consumer sets this header on every public read request:")
    print(f"   x-api-key: {raw_key}\n")
    print(f"   Hash stored in DB: {key_hash[:16]}...\n")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Issue an NGX Advisory API Key instance")
    ap.add_argument("--owner", required=True, help="Consumer application description namespace identifier context")
    args = ap.parse_args()
    generate_key(args.owner)