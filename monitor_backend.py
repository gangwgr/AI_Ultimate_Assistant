#!/usr/bin/env python3
"""
Monitor backend logs in real-time
"""

import subprocess
import sys
import time
import os

def monitor_backend():
    """Monitor backend server logs"""
    
    print("🔍 Backend Log Monitor")
    print("=" * 60)
    print("Monitoring backend logs in real-time...")
    print("Press Ctrl+C to stop monitoring")
    print("=" * 60)
    
    try:
        # Check if server is running
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'start_optimized.py' not in result.stdout:
            print("❌ Server not running. Starting server...")
            subprocess.Popen(['python', 'start_optimized.py'], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.STDOUT)
            time.sleep(3)
        
        # Monitor server output
        while True:
            # Get recent server output
            try:
                # Try to get server process
                ps_result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                server_lines = [line for line in ps_result.stdout.split('\n') 
                              if 'start_optimized.py' in line and 'grep' not in line]
                
                if server_lines:
                    print(f"✅ Server is running (PID: {server_lines[0].split()[1]})")
                    print(f"📊 Server status: {'🟢 Active' if len(server_lines) > 0 else '🔴 Inactive'}")
                else:
                    print("❌ Server not found")
                
                # Check for recent log files
                log_files = []
                for root, dirs, files in os.walk('.'):
                    for file in files:
                        if file.endswith('.log'):
                            log_files.append(os.path.join(root, file))
                
                if log_files:
                    print(f"📝 Found log files: {log_files}")
                    for log_file in log_files:
                        try:
                            with open(log_file, 'r') as f:
                                lines = f.readlines()
                                if lines:
                                    print(f"\n📄 Recent logs from {log_file}:")
                                    for line in lines[-5:]:  # Last 5 lines
                                        print(f"   {line.strip()}")
                        except Exception as e:
                            print(f"   ❌ Error reading {log_file}: {e}")
                
                print("\n" + "-" * 60)
                print("🔄 Monitoring... (Press Ctrl+C to stop)")
                print("💡 Try using the PR reviewer UI now:")
                print("   http://127.0.0.1:8000/frontend/pr_reviewer.html")
                print("-" * 60)
                
                time.sleep(10)  # Check every 10 seconds
                
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Error monitoring: {e}")
                time.sleep(5)
                
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped")
    except Exception as e:
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    monitor_backend()
