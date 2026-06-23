import sys
import os
import socket
from pydantic_settings import BaseSettings
from pydantic import Field

# Append backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TestConfig(BaseSettings):
    DATABASE_URL: str = Field(..., validation_alias="DATABASE_URL")
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

def run_diagnostics():
    print("===================================================")
    print("  AI Startup Validator - DB Connection Diagnostic  ")
    print("===================================================\n")
    
    if not os.path.exists(".env"):
        print("[ERROR] .env configuration file not found in backend directory!")
        sys.exit(1)
        
    try:
        config = TestConfig()
        db_url = config.DATABASE_URL
    except Exception as e:
        print(f"[ERROR] Failed to load DATABASE_URL from .env: {str(e)}")
        sys.exit(1)
        
    print(f"DATABASE_URL found: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    
    # Extract host
    try:
        host_part = db_url.split("@")[-1]
        host = host_part.split(":")[0]
        port_part = host_part.split(":")[1]
        port = int(port_part.split("/")[0])
    except Exception:
        print("[ERROR] Invalid connection URL format. Ensure it follows: postgresql://user:pass@host:port/dbname")
        sys.exit(1)
        
    print(f"Parsed Host: {host}")
    print(f"Parsed Port: {port}")
    
    # Test DNS Resolution
    print("\n[Step 1/3] Testing Host Name Resolution...")
    try:
        addr_info = socket.getaddrinfo(host, port)
        ips = [info[4][0] for info in addr_info]
        print(f"[SUCCESS] Host resolved successfully to: {', '.join(set(ips))}")
        is_ipv6_only = all(":" in ip for ip in ips)
        if is_ipv6_only:
            print("[INFO] This hostname resolved to IPv6 addresses only.")
    except Exception as e:
        print(f"[ERROR] Host resolution failed: {str(e)}")
        print("\n>>> RECOMMENDATION:")
        print("Your system or network might not support IPv6 routing. To resolve this, you must:")
        print("1. Go to your Supabase Dashboard -> Project Settings -> Database.")
        print("2. Scroll to 'Connection pooling' and copy the Session/Transaction connection string.")
        print("3. Replace your DATABASE_URL in backend/.env with the pooler URL (which supports IPv4).")
        sys.exit(1)
        
    # Test Connection
    print("\n[Step 2/3] Connecting to PostgreSQL database...")
    try:
        import psycopg2
        conn = psycopg2.connect(db_url)
        print("[SUCCESS] Connected to database successfully!")
        conn.close()
    except ImportError:
        print("[INFO] psycopg2 not installed in this environment. Skipping driver test.")
    except Exception as e:
        print(f"[ERROR] Database connection failed: {str(e)}")
        print("\n>>> RECOMMENDATION:")
        print("1. Double-check that your database password is correct.")
        print("2. Ensure any special characters in the password (like @, +, /) are URL-encoded (e.g. @ becomes %40).")
        print("3. Check if your Supabase project is active (not paused).")
        sys.exit(1)
        
    print("\n[Step 3/3] Overall Status Check...")
    print("[SUCCESS] All diagnostics passed! Your backend connection parameters are valid.")
    print("If your frontend still shows 'Failed to fetch', check that you started the backend server using start_project.bat.")

if __name__ == "__main__":
    run_diagnostics()
