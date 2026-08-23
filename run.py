import os
import subprocess
import sys
import signal
import time


def main():
    print("Starting Meeting Summarizer...")

    # start backend
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000"],
        preexec_fn=os.setsid,
    )

    time.sleep(1.5)

    # start frontend
    frontend = subprocess.Popen(
        [sys.executable, "frontend/app.py"],
        preexec_fn=os.setsid,
    )

    print("-" * 35)
    print("Frontend: http://localhost:5000")
    print("API Docs: http://localhost:8000/docs")
    print("Press Ctrl+C to stop")
    print("-" * 35)

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
