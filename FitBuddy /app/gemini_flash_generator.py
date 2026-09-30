from app.gemini_client import generate_text

def generate_nutrition_tip_with_flash(goal: str) -> str:
    prompt = f'''
Give one concise, practical nutrition or recovery tip for a person whose fitness goal is:
{goal}

Keep it general, safe, and easy to understand. Do not provide medical diagnosis or treatment.
'''
    return generate_text(prompt)
