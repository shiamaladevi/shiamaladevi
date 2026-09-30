from app.gemini_client import generate_text

def generate_fitness_plan(goal: str, intensity: str, age: int, weight: float) -> tuple[str, str]:
    prompt = f'''
Create a practical, personalized 7-day fitness plan and one concise nutrition or recovery tip.

User:
- Age: {age}
- Weight: {weight} kg
- Fitness goal: {goal}
- Workout intensity: {intensity}

Include a 5-10 minute warm-up, exercises with sets/reps or duration, recovery guidance, and a short
general safety note. Keep the plan suitable for the stated intensity. Do not use a table.

Return exactly these two sections:
WORKOUT PLAN:
[Day 1 through Day 7 plan]

NUTRITION TIP:
[One concise, general, safe tip. No medical diagnosis or treatment.]
'''
    response = generate_text(prompt)
    plan_section, separator, tip_section = response.partition("NUTRITION TIP:")
    if not separator:
        plan_section, separator, tip_section = response.partition("Nutrition tip:")
    workout = plan_section.removeprefix("WORKOUT PLAN:").strip()
    tip = tip_section.strip() if separator else "Stay hydrated and include protein and colorful produce in meals to support recovery."
    if not workout:
        raise RuntimeError("Gemini returned no workout plan")
    return workout, tip

def generate_workout_gemini(goal: str, intensity: str, age: int, weight: float) -> str:
    prompt = f'''
Create a personalized 7-day fitness plan.

User:
- Age: {age}
- Weight: {weight} kg
- Fitness goal: {goal}
- Workout intensity: {intensity}

Requirements:
- Give Day 1 through Day 7.
- Include warm-up (5-10 minutes).
- Include main workout with exercise names, sets/reps or duration.
- Include rest/recovery guidance.
- Keep the plan practical and easy to follow.
- Add a short general safety note.
- Return plain text with clear headings. Do not use markdown tables.
'''
    return generate_text(prompt)
