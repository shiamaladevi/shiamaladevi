from app.gemini_client import generate_text

def update_workout_plan(original_plan: str, feedback: str) -> str:
    prompt = f'''
Update the following 7-day workout plan according to the user's feedback.

ORIGINAL PLAN:
{original_plan}

USER FEEDBACK:
{feedback}

Return a complete revised 7-day plan. Preserve useful parts, apply the feedback where reasonable,
keep a clear day-by-day format, and include a short general safety note.
'''
    return generate_text(prompt)
