import os
import requests
from flask import Flask, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
API_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")


@app.route("/")
def index():
    try:
        resp = requests.get(f"{API_URL}/meetings", timeout=5)
        meetings = resp.json() if resp.ok else []
    except requests.ConnectionError:
        meetings = []
    return render_template("index.html", meetings=meetings)


@app.route("/meeting/<int:meeting_id>")
def meeting_detail(meeting_id):
    try:
        resp = requests.get(f"{API_URL}/meetings/{meeting_id}", timeout=5)
        if not resp.ok:
            return render_template("meeting.html", meeting=None, error="Meeting not found")
        meeting = resp.json()
    except requests.ConnectionError:
        return render_template("meeting.html", meeting=None, error="Can't reach the backend API. Is it running?")
    return render_template("meeting.html", meeting=meeting)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
