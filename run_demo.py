#!/usr/bin/env python3
"""
Demo runner script to start both FastAPI backend and Streamlit frontend
"""

import subprocess
import sys
import time
import threading
import requests
import os
from pathlib import Path

def check_port_available(port):
    """Check if a port is available"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=2)
        return False  # Port is in use
    except requests.exceptions.RequestException:
        return True  # Port is available

def run_fastapi():
    """Run the FastAPI backend"""
    print("🚀 Starting FastAPI backend on http://localhost:8000")
    
    try:
        # Run uvicorn with the app
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app:app", 
            "--reload", 
            "--host", "0.0.0.0",
            "--port", "8000"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start FastAPI: {e}")
    except KeyboardInterrupt:
        print("\n🛑 FastAPI stopped by user")

def run_streamlit():
    """Run the Streamlit frontend"""
    print("🎨 Starting Streamlit frontend on http://localhost:8501")
    
    try:
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", 
            "run", "nutrition_frontend.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Streamlit: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Streamlit stopped by user")

def wait_for_api():
    """Wait for the API to be ready"""
    print("⏳ Waiting for FastAPI to start...")
    
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print("✅ FastAPI is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(1)
        print(f"   Still waiting... ({i+1}/30)")
    
    print("❌ FastAPI failed to start in time")
    return False

def install_requirements():
    """Install required packages"""
    print("📦 Installing requirements...")
    
    requirements = [
        "streamlit>=1.28.0",
        "requests>=2.31.0", 
        "pandas>=2.0.0",
        "plotly>=5.15.0",
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "pydantic>=2.4.0",
        "spacy>=3.6.0",
        "word2number>=2.0.0"
    ]
    
    for req in requirements:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", req], 
                         check=True, capture_output=True)
            print(f"✅ Installed {req}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {req}")

def main():
    """Main demo runner"""
    print("=" * 60)
    print("🥗 NUTRI-VISION DEMO LAUNCHER")
    print("=" * 60)
    
    # Check if required files exist
    required_files = ["app.py", "nutrition_frontend.py"]
    missing_files = [f for f in required_files if not Path(f).exists()]
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        print("Make sure you're in the correct directory with all the project files.")
        return
    
    # Check if ports are available
    if not check_port_available(8000):
        print("⚠️  Port 8000 is already in use. Stop the existing FastAPI server or use a different port.")
        
    if not check_port_available(8501):
        print("⚠️  Port 8501 is already in use. Stop the existing Streamlit server or use a different port.")
    
    print("\nSelect an option:")
    print("1. 🚀 Start FastAPI backend only")
    print("2. 🎨 Start Streamlit frontend only (requires backend running)")
    print("3. 🔄 Start both (recommended)")
    print("4. 📦 Install requirements only")
    print("5. 🧪 Run tests")
    print("0. ❌ Exit")
    
    choice = input("\nEnter your choice (0-5): ").strip()
    
    if choice == "0":
        print("👋 Goodbye!")
        return
    
    elif choice == "1":
        run_fastapi()
    
    elif choice == "2":
        run_streamlit()
    
    elif choice == "3":
        print("\n🔄 Starting both FastAPI and Streamlit...")
        
        # Start FastAPI in a separate thread
        api_thread = threading.Thread(target=run_fastapi, daemon=True)
        api_thread.start()
        
        # Wait for API to be ready
        if wait_for_api():
            # Start Streamlit in main thread
            run_streamlit()
        else:
            print("❌ Cannot start Streamlit without FastAPI")
    
    elif choice == "4":
        install_requirements()
        print("✅ Requirements installation complete!")
    
    elif choice == "5":
        print("🧪 Running tests...")
        try:
            subprocess.run([sys.executable, "test_system.py"], check=True)
        except subprocess.CalledProcessError:
            print("❌ Tests failed")
        except FileNotFoundError:
            print("❌ test_system.py not found")
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo stopped by user. Goodbye!")