#!/usr/bin/env python3
"""
Generate self-signed SSL certificates for local HTTPS development
"""

import os
import subprocess
import sys

def generate_ssl_certificates():
    """Generate self-signed SSL certificates for localhost"""
    
    # Create ssl directory
    os.makedirs("ssl", exist_ok=True)
    
    cert_path = "ssl/cert.pem"
    key_path = "ssl/key.pem"
    
    # Check if certificates already exist
    if os.path.exists(cert_path) and os.path.exists(key_path):
        print("✅ SSL certificates already exist!")
        return True
    
    print("🔐 Generating SSL certificates for localhost...")
    
    try:
        # Generate private key and certificate
        cmd = [
            "openssl", "req", "-x509", "-newkey", "rsa:4096", 
            "-keyout", key_path, "-out", cert_path,
            "-days", "365", "-nodes",
            "-subj", "/C=US/ST=CA/L=San Francisco/O=AI Assistant/CN=localhost"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ SSL certificates generated successfully!")
            print(f"📄 Certificate: {cert_path}")
            print(f"🔑 Private key: {key_path}")
            print("\n⚠️  Browser will show security warning for self-signed cert")
            print("   Click 'Advanced' → 'Proceed to localhost (unsafe)' to continue")
            return True
        else:
            print(f"❌ Error generating certificates: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ OpenSSL not found. Please install OpenSSL:")
        print("   macOS: brew install openssl")
        print("   Ubuntu: sudo apt-get install openssl")
        print("   Windows: Download from https://slproweb.com/products/Win32OpenSSL.html")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def update_env_for_https():
    """Update .env file to enable HTTPS"""
    try:
        env_path = ".env"
        if not os.path.exists(env_path):
            print("❌ .env file not found")
            return False
        
        # Read current .env
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Update or add HTTPS settings
        updated_lines = []
        https_updated = False
        redirect_updated = False
        
        for line in lines:
            if line.startswith('use_https='):
                updated_lines.append('use_https=true\n')
                https_updated = True
            elif line.startswith('GOOGLE_REDIRECT_URI='):
                updated_lines.append('GOOGLE_REDIRECT_URI=https://localhost:8443/api/auth/google/callback\n')
                redirect_updated = True
            else:
                updated_lines.append(line)
        
        # Add if not exist
        if not https_updated:
            updated_lines.append('use_https=true\n')
        if not redirect_updated:
            updated_lines.append('GOOGLE_REDIRECT_URI=https://localhost:8443/api/auth/google/callback\n')
        
        # Write back
        with open(env_path, 'w') as f:
            f.writelines(updated_lines)
        
        print("✅ Updated .env file for HTTPS")
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env: {e}")
        return False

if __name__ == "__main__":
    print("🔒 Setting up HTTPS for AI Ultimate Assistant")
    print("=" * 50)
    
    if generate_ssl_certificates():
        if update_env_for_https():
            print("\n🎉 HTTPS setup complete!")
            print("\n📋 Next steps:")
            print("1. Update Google Cloud Console redirect URI to:")
            print("   https://localhost:8443/api/auth/google/callback")
            print("2. Restart the backend server: python main.py")
            print("3. Access your app at: https://localhost:8443")
            print("\n⚠️  Your browser will show a security warning")
            print("   This is normal for self-signed certificates")
        else:
            print("❌ Failed to update .env file")
    else:
        print("❌ Failed to generate SSL certificates") 