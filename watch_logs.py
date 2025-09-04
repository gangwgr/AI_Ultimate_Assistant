#!/usr/bin/env python3
"""
Watch server logs in real-time
"""

import subprocess
import sys
import time

def watch_logs():
    """Watch server logs in real-time"""
    
    print("🔍 Real-time Backend Log Monitor")
    print("=" * 60)
    print("Watching for backend activity...")
    print("💡 Now try using the PR reviewer UI:")
    print("   http://127.0.0.1:8000/frontend/pr_reviewer.html")
    print("=" * 60)
    
    try:
        # Start monitoring with curl to check server health
        while True:
            try:
                # Check server health
                result = subprocess.run(['curl', '-s', 'http://127.0.0.1:8000/api/health'], 
                                      capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    print(f"✅ Server is healthy - {time.strftime('%H:%M:%S')}")
                else:
                    print(f"⚠️  Server health check failed - {time.strftime('%H:%M:%S')}")
                
                # Check if server process is still running
                ps_result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                if 'start_optimized.py' in ps_result.stdout:
                    print(f"🟢 Server process active - {time.strftime('%H:%M:%S')}")
                else:
                    print(f"🔴 Server process not found - {time.strftime('%H:%M:%S')}")
                
                print("-" * 40)
                time.sleep(5)
                
            except subprocess.TimeoutExpired:
                print(f"⏰ Health check timeout - {time.strftime('%H:%M:%S')}")
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(5)
                
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")

if __name__ == "__main__":
    watch_logs()
