from google import genai
from backend.config import GEMINI_API_KEY, GEMINI_MODEL

# prompt to get a structured meeting summary
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
- [ ] [Action item] — Assigned to: [Person] — Deadline: [Date if mentioned]

### Unresolved Issues
- [Issue that needs follow-up]

Meeting Transcript:
{transcript}
"""

# separate prompt just for action items — gives better results than
# trying to parse them out of the full summary
ACTION_ITEMS_PROMPT = """Extract ONLY the action items from this meeting transcript.
For each action item identify:
- The task description
- Who its assigned to (if mentioned)  
- The deadline (if mentioned)

Format each as: "- [ ] [Task] — Assigned to: [Person] — Deadline: [Date]"
If assignee or deadline is unknown, write "Not specified".

Transcript:
{transcript}
"""


def _generate_with_fallback(client, prompt):
    """try the requested gemini model, falling back to other models if unavailable"""
    models_to_try = [
        GEMINI_MODEL,
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-flash-latest",
        "gemini-3.7-flash",
    ]
    seen = set()
    candidate_models = [m for m in models_to_try if not (m in seen or seen.add(m))]

    last_err = None
    for model_name in candidate_models:
        try:
            print(f"[*] Calling Gemini with model: {model_name}")
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if resp.text:
                return resp.text.strip()
        except Exception as e:
            last_err = e
            print(f"[!] Model {model_name} failed: {e}. Trying fallback...")

    raise last_err or RuntimeError("Failed to generate summary with Gemini")


def summarize_transcript(transcript):
    """send transcript to gemini and get back a structured summary + action items"""

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set! Add it to your .env file.")

    if not transcript or not transcript.strip():
        raise ValueError("Transcript is empty, nothing to summarize")

    client = genai.Client(api_key=GEMINI_API_KEY)

    # get the full summary
    print("[*] Generating summary with Gemini...")
    summary_text = _generate_with_fallback(
        client, SUMMARY_PROMPT.format(transcript=transcript)
    )

    # get action items separately for better extraction
    print("[*] Extracting action items...")
    actions_text = _generate_with_fallback(
        client, ACTION_ITEMS_PROMPT.format(transcript=transcript)
    )

    return {
        "summary": summary_text,
        "action_items": actions_text,
    }
