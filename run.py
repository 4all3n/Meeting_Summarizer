"""
Script to start both the backend (FastAPI) and frontend (Flask) servers.
Run with: python run.py
"""

import os
import subprocess
import sys
import signal
import time


def main():
    print("Starting Meeting Summarizer...")
    print("-" * 40)

    # start fastapi backend in its own process group so we can kill all child workers cleanly
    print("Starting backend on http://localhost:8000")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000"],
        preexec_fn=os.setsid,
    )

    time.sleep(1.5)

    # start flask frontend in its own process group
    print("Starting frontend on http://localhost:5000")
    frontend = subprocess.Popen(
        [sys.executable, "frontend/app.py"],
        preexec_fn=os.setsid,
    )

    print("-" * 40)
    print("Both servers running!")
    print("  Frontend:  http://localhost:5000")
    print("  API Docs:  http://localhost:8000/docs")
    print("  Ctrl+C to stop")
    print("-" * 40)

    def stop(sig=None, frame=None):
        print("\nStopping servers...")
        for p in [backend, frontend]:
            try:
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            except Exception:
                pass
        time.sleep(0.5)
        for p in [backend, frontend]:
            try:
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            except Exception:
                pass
        sys.exit(0)

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop()


if __name__ == "__main__":
    main()
