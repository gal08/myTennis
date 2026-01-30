"""
🔍 Simple connection test
Run this AFTER starting Server.py
"""
import socket
import time

print("🔍 Testing connection to server...")
print("="*60)

try:
    # Create socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("✅ Socket created")

    # Connect
    print("📡 Connecting to 127.0.0.1:5000...")
    client.connect(("127.0.0.1", 5000))
    print("✅ CONNECTED!")

    # Wait a bit
    print("⏳ Waiting 2 seconds...")
    time.sleep(2)

    # Close
    print("🔌 Closing connection...")
    client.close()
    print("✅ Done!")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("="*60)
print("\n👀 Now check the Server terminal - did it print anything?")