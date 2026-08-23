from google import genai
from backend.config import GEMINI_API_KEY, GEMINI_MODEL

SUMMARY_PROMPT = """You are an expert meeting analyst. Analyze the following meeting transcript and provide a structured summary.

Instructions:
1. Identify the main topics discussed
2. Extract key decisions that were made
3. List specific action items with assignees (if mentioned)
4. Note any deadlines or timelines mentioned
5. Highlight any unresolved issues or open questions

Use this exact output format:

### Meeting Summary
[2-3 paragraph overview of the meeting]

### Key Decisions
- [Decision 1]
- [Decision 2]

### Action Items
- [Action item] — Assigned to: [Person] — Deadline: [Date if mentioned]

### Unresolved Issues
- [Issue that needs follow-up]

Meeting Transcript:
{transcript}
"""

ACTION_ITEMS_PROMPT = """Extract ONLY the action items from this meeting transcript.
For each action item identify:
- The task description
- Who its assigned to (if mentioned)  
- The deadline (if mentioned)

Format each as: "- [Task] — Assigned to: [Person] — Deadline: [Date]"
If assignee or deadline is unknown, write "Not specified".

Transcript:
{transcript}
"""


def _call_gemini(client, prompt):
    """try configured model first, fall back to gemini-2.0-flash"""
    models = [GEMINI_MODEL]
    if GEMINI_MODEL != "gemini-2.0-flash":
        models.append("gemini-2.0-flash")

    last_err = None
    for model in models:
        try:
            print(f"trying model: {model}")
            resp = client.models.generate_content(model=model, contents=prompt)
            if resp.text:
                return resp.text.strip()
        except Exception as e:
            last_err = e
            print(f"{model} failed: {e}")

    raise last_err or RuntimeError("all gemini models failed")


def summarize_transcript(transcript):
    """send transcript to gemini and get back summary + action items"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in .env")

    if not transcript or not transcript.strip():
        raise ValueError("empty transcript, nothing to summarize")

    client = genai.Client(api_key=GEMINI_API_KEY)

    print("generating summary...")
    summary = _call_gemini(client, SUMMARY_PROMPT.format(transcript=transcript))

    print("extracting action items...")
    actions = _call_gemini(client, ACTION_ITEMS_PROMPT.format(transcript=transcript))

    return {"summary": summary, "action_items": actions}
