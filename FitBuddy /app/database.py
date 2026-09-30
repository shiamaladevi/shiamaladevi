import os
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{Path(__file__).resolve().parent.parent / 'fitbuddy.db'}")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    goal = Column(String(100), nullable=False)
    intensity = Column(String(30), nullable=False)

class WorkoutPlan(Base):
    __tablename__ = "workout_plans"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, index=True, nullable=False)
    original_plan = Column(Text, nullable=False)
    updated_plan = Column(Text, nullable=True)
    nutrition_tip = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)

def save_user(user_id, username, age, weight, goal, intensity):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            user.username, user.age, user.weight = username, age, weight
            user.goal, user.intensity = goal, intensity
        else:
            db.add(User(user_id=user_id, username=username, age=age, weight=weight,
                        goal=goal, intensity=intensity))
        db.commit()
    finally:
        db.close()

def save_plan(user_id, original_plan, nutrition_tip):
    db = SessionLocal()
    try:
        plan = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user_id).first()
        if plan:
            plan.original_plan, plan.updated_plan = original_plan, None
            plan.nutrition_tip, plan.feedback = nutrition_tip, None
        else:
            db.add(WorkoutPlan(user_id=user_id, original_plan=original_plan,
                               nutrition_tip=nutrition_tip))
        db.commit()
    finally:
        db.close()

def get_original_plan(user_id):
    db = SessionLocal()
    try:
        plan = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user_id).first()
        return plan.original_plan if plan else None
    finally:
        db.close()

def update_plan(user_id, updated_plan, feedback):
    db = SessionLocal()
    try:
        plan = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user_id).first()
        if not plan:
            return False
        plan.updated_plan, plan.feedback = updated_plan, feedback
        db.commit()
        return True
    finally:
        db.close()

def get_user(user_id):
    db = SessionLocal()
    try:
        return db.query(User).filter(User.user_id == user_id).first()
    finally:
        db.close()

def get_all_records():
    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.id.desc()).all()
        plans = {p.user_id: p for p in db.query(WorkoutPlan).all()}
        return [(u, plans.get(u.user_id)) for u in users]
    finally:
        db.close()
