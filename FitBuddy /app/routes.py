import logging
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from pydantic import ValidationError
from app.schemas import UserInput, FeedbackRequest
from app.database import save_user, save_plan, get_original_plan, update_plan, get_user, get_all_records
from app.gemini_generator import generate_fitness_plan
from app.updated_plan import update_workout_plan

router = APIRouter()
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})

@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout(request: Request, username: str = Form(...), user_id: str = Form(...),
                     age: int = Form(...), weight: float = Form(...),
                     goal: str = Form(...), intensity: str = Form(...)):
    try:
        data = UserInput(username=username, user_id=user_id, age=age, weight=weight,
                         goal=goal, intensity=intensity)
    except ValidationError as exc:
        return templates.TemplateResponse(request=request, name="index.html",
            context={"error": exc.errors()[0]["msg"]}, status_code=422)
    ai_notice = None
    try:
        workout_plan, nutrition_tip = generate_fitness_plan(data.goal, data.intensity, data.age, data.weight)
    except Exception as exc:
        logger.exception("Gemini workout generation failed")
        workout_plan = _basic_workout(data.goal, data.intensity)
        ai_notice = f"Gemini could not generate the plan, so a basic starter plan is shown. {_gemini_failure_hint(exc)}"
    if ai_notice:
        nutrition_tip = "Drink water regularly, include protein and colorful produce in meals, and get enough sleep to support recovery."
    save_user(data.user_id, data.username, data.age, data.weight, data.goal, data.intensity)
    save_plan(data.user_id, workout_plan, nutrition_tip)
    return templates.TemplateResponse(request=request, name="result.html", context={**data.model_dump(),
        "workout_plan": workout_plan, "nutrition_tip": nutrition_tip,
        "updated_plan": None, "message": ai_notice})

@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback(request: Request, user_id: str = Form(...), feedback: str = Form(...)):
    try:
        data = FeedbackRequest(user_id=user_id, feedback=feedback)
    except ValidationError as exc:
        return templates.TemplateResponse(request=request, name="result.html",
            context={"user_id": user_id, "message": exc.errors()[0]["msg"]}, status_code=422)
    user = get_user(data.user_id)
    original_plan = get_original_plan(data.user_id)
    if not user or not original_plan:
        return templates.TemplateResponse(request=request, name="result.html",
            context={"message": "User ID not found. Generate a plan first."},
            status_code=404)
    try:
        updated = update_workout_plan(original_plan, data.feedback)
        message = "Your plan has been updated based on your feedback!"
    except Exception as exc:
        logger.exception("Gemini feedback revision failed")
        updated = (f"{original_plan}\n\nRequested feedback: {data.feedback}\n\n"
                   "AI revision is currently unavailable. Use this note to adjust the plan conservatively, "
                   "or try submitting again when the AI service is available.")
        message = f"AI revision is unavailable. {_gemini_failure_hint(exc)}"
    update_plan(data.user_id, updated, data.feedback)
    return templates.TemplateResponse(request=request, name="result.html", context={
        "username": user.username, "user_id": user.user_id, "age": user.age,
        "weight": user.weight, "goal": user.goal, "intensity": user.intensity,
        "workout_plan": original_plan,
        "nutrition_tip": "Your feedback is saved with this plan.",
        "updated_plan": updated,
        "message": message})

@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request):
    return templates.TemplateResponse(request=request, name="all_users.html",
        context={"records": get_all_records()})

def _gemini_failure_hint(exc: Exception) -> str:
    """Translate common Gemini failures without exposing credentials or raw responses."""
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    try:
        status = int(code)
    except (TypeError, ValueError):
        status = None
    detail = str(exc).lower()

    if status == 401 or "api key not valid" in detail or "unauthenticated" in detail:
        return "Google rejected the API key. Replace GOOGLE_API_KEY in .env with a Gemini API key."
    if status == 403 or "permission_denied" in detail or "api_key_service_blocked" in detail:
        return "The key or project is not allowed to use Gemini. Restrict the key to the Gemini API or create a new AI Studio key."
    if status == 429 or "resource_exhausted" in detail or "quota" in detail or "rate limit" in detail:
        return "Gemini quota or rate limit was reached. Check API usage and try again later."
    if status == 404 or "not_found" in detail or "model" in detail and "not found" in detail:
        return "The configured model was not found or is unavailable to this key. Check GEMINI_MODEL in .env."
    if status is not None and status >= 500:
        return f"Google's Gemini service returned HTTP {status}, including the backup model. Try again shortly or check Google's API status."
    return f"Gemini request failed ({type(exc).__name__}). See the Uvicorn terminal for details."

def _basic_workout(goal: str, intensity: str) -> str:
    effort = {"low": "2 rounds at a comfortable pace", "medium": "3 rounds at a steady pace",
              "high": "4 rounds; stop if your form slips"}.get(intensity, "2 comfortable rounds")
    days = [
        "Full body: chair squats, incline push-ups, glute bridges, and bird-dogs (8–12 reps each).",
        "Cardio: brisk walking or cycling for 20–30 minutes.",
        "Mobility and recovery: gentle stretching and a relaxed walk.",
        "Strength: reverse lunges, backpack rows, hip hinges, and dead bugs (8–12 reps each).",
        "Cardio: 20–30 minutes at a conversational pace.",
        "Full body: repeat Day 1 with comfortable variations.",
        "Rest: gentle walking or complete rest."
    ]
    plan = [f"Day {i}: {work} {effort if i in (1, 4, 6) else ''}".strip()
            for i, work in enumerate(days, 1)]
    plan.append(f"\nGoal: {goal}. Warm up for 5 minutes and cool down after activity. Adjust to your ability; stop if you feel pain, dizziness, or unusual shortness of breath.")
    return "\n".join(plan)
