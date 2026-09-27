"""
PocketSmart AI - FastAPI Main Application Engine (Backend)
Empowers lifestyle budget planning for Home Interior, Party & Event, and Haute Joaillerie Styling.
"""

import os
import sys
from pathlib import Path

# Ensure root directory is in sys.path for shared services
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import uvicorn
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from services.auth_service import (
    register_user,
    authenticate_user,
    validate_session,
    revoke_session,
    save_recommendation_history,
    get_user_history
)
from services.planner_service import (
    generate_home_plan,
    generate_party_plan,
    generate_jewelry_plan,
    generate_travel_plan,
    generate_tech_plan,
    generate_wedding_plan,
    generate_grocery_plan,
    generate_student_plan
)

app_state: Dict[str, Any] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    app_state["status"] = "operational"
    app_state["services_loaded"] = [
        "auth", "gemini_engine", "home_planner", "party_planner", 
        "jewelry_planner", "travel_planner", "tech_planner", 
        "wedding_planner", "grocery_planner", "student_planner"
    ]
    app_state["gemini_configured"] = bool(os.getenv("GEMINI_API_KEY"))
    print("[PocketSmart AI] Application backend services initialized successfully on startup.")
    yield
    print("[PocketSmart AI] Application backend services shutting down.")

app = FastAPI(
    title="PocketSmart AI™ Lifestyle Budget Engine",
    description="Autonomous AI-driven budget optimization and multi-store recommendation engine across real-world spending domains.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files & Templates directory mapping
STATIC_DIR = os.path.join(ROOT_DIR, "frontend", "static")
TEMPLATES_DIR = os.path.join(ROOT_DIR, "frontend", "templates")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR if os.path.exists(TEMPLATES_DIR) else os.path.join(ROOT_DIR, "templates"))


# -------------------------------------------------------------
# Pydantic Request Models
# -------------------------------------------------------------

class RegisterRequest(BaseModel):
    full_name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="Password (min 6 chars)")
    currency: Optional[str] = Field("$", description="Currency symbol ($ or ₹)")

class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")

class HomePlanRequest(BaseModel):
    room_type: str = Field(..., description="Room type: Living Room, Bedroom, Kitchen, Office, Balcony")
    style_preference: str = Field(..., description="Aesthetic style (e.g. Modern Minimalist, Scandinavian)")
    budget: float = Field(..., gt=0, description="Total budget ceiling")
    currency: Optional[str] = Field("$", description="Currency symbol")
    space_size: Optional[str] = Field("Standard (14x18 ft)", description="Room dimensions")
    custom_notes: Optional[str] = Field("", description="Specific priorities")

class PartyPlanRequest(BaseModel):
    event_type: str = Field(..., description="Event classification")
    guest_count: int = Field(..., gt=0, description="Number of expected guests")
    budget: float = Field(..., gt=0, description="Total celebration budget")
    currency: Optional[str] = Field("$", description="Currency symbol")
    theme_preference: Optional[str] = Field("Modern Neon & Cocktail Loft", description="Theme aesthetic")
    custom_notes: Optional[str] = Field("", description="Dietary or venue specifications")

class JewelryPlanRequest(BaseModel):
    occasion: str = Field(..., description="Occasion: Wedding, Cocktail Gala, Festive")
    outfit_style: str = Field(..., description="Outfit color and silhouette")
    metal_preference: str = Field(..., description="Preferred metal: 22K Gold, 18K Rose Gold, Platinum")
    budget: float = Field(..., gt=0, description="Jewelry budget ceiling")
    currency: Optional[str] = Field("$", description="Currency symbol")
    image_base64: Optional[str] = Field(None, description="Optional base64 encoded outfit photo for multimodal analysis")
    image_mime_type: Optional[str] = Field("image/jpeg", description="MIME type of uploaded image")
    custom_notes: Optional[str] = Field("", description="Custom styling details")

class TravelPlanRequest(BaseModel):
    destination: str = Field(..., description="Target destination")
    duration_days: int = Field(..., gt=0, description="Trip duration in days")
    travelers_count: int = Field(..., gt=0, description="Number of travelers")
    budget: float = Field(..., gt=0, description="Total trip budget ceiling")
    currency: Optional[str] = Field("$", description="Currency symbol")
    travel_style: Optional[str] = Field("Boutique Adventure", description="Style: Luxury / Boutique / Backpacker")
    custom_notes: Optional[str] = Field("", description="Specific travel notes")

class TechPlanRequest(BaseModel):
    workflow_type: str = Field(..., description="Workflow: Software Dev, Video Editing, Remote Productivity")
    form_factor: str = Field(..., description="Form factor: Laptop + Monitor, Desktop, Mobile")
    budget: float = Field(..., gt=0, description="Hardware budget ceiling")
    currency: Optional[str] = Field("$", description="Currency symbol")
    custom_notes: Optional[str] = Field("", description="Brand or ecosystem preference")

class WeddingPlanRequest(BaseModel):
    event_scale: str = Field(..., description="Event scale: Intimate (50), Grand (200), Destination")
    guest_count: int = Field(..., gt=0, description="Guest count")
    budget: float = Field(..., gt=0, description="Total wedding capital budget")
    currency: Optional[str] = Field("$", description="Currency symbol")
    cultural_theme: Optional[str] = Field("Contemporary Fusion", description="Theme / Traditions")
    custom_notes: Optional[str] = Field("", description="Specific requests")

class GroceryPlanRequest(BaseModel):
    household_size: int = Field(..., gt=0, description="Household member count")
    dietary_regime: str = Field(..., description="Diet: High Protein, Mediterranean, Vegan, Keto")
    weekly_budget: float = Field(..., gt=0, description="Weekly grocery allocation")
    currency: Optional[str] = Field("$", description="Currency symbol")
    custom_notes: Optional[str] = Field("", description="Allergies or preferences")

class StudentPlanRequest(BaseModel):
    academic_level: str = Field(..., description="Level: Undergrad / Master's / PhD")
    monthly_allowance: float = Field(..., gt=0, description="Monthly student budget")
    currency: Optional[str] = Field("$", description="Currency symbol")
    city_tier: Optional[str] = Field("Metropolitan Hub", description="City cost tier")
    custom_notes: Optional[str] = Field("", description="Roommate or campus notes")


# -------------------------------------------------------------
# Dependency: Extract Current User
# -------------------------------------------------------------

def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "").strip()
    return validate_session(token)


# -------------------------------------------------------------
# Primary Frontend Route
# -------------------------------------------------------------

@app.get("/", response_class=HTMLResponse, summary="Main Landing & Application UI")
async def serve_home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


# -------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------

@app.get("/startup", summary="Initialize and check application service health")
async def startup_check():
    """Initializes essential application services and loads configuration settings."""
    if "status" not in app_state:
        app_state["status"] = "operational"
        app_state["services_loaded"] = ["auth", "gemini_engine", "home_planner", "party_planner", "jewelry_planner"]
        app_state["gemini_configured"] = bool(os.getenv("GEMINI_API_KEY"))
    return {
        "status": app_state.get("status", "operational"),
        "services_loaded": app_state.get("services_loaded", []),
        "gemini_ready": app_state.get("gemini_configured", False),
        "timestamp": os.getenv("APP_ENV", "production")
    }


# --- Authentication & Session Routes ---

@app.post("/register", summary="User Registration")
async def register(payload: RegisterRequest):
    """Allows new users to create an account to access personalized recommendations."""
    res = register_user(
        full_name=payload.full_name,
        email=payload.email,
        password=payload.password,
        currency=payload.currency or "$"
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res


@app.post("/login", summary="User Authentication & Login")
async def login(payload: LoginRequest):
    """Authenticates existing users to access dashboard and saved data."""
    res = authenticate_user(email=payload.email, password=payload.password)
    if not res.get("success"):
        raise HTTPException(status_code=401, detail=res.get("message"))
    return res


@app.post("/logout", summary="User Session Logout")
@app.get("/logout", summary="User Session Logout")
async def logout(authorization: Optional[str] = Header(None)):
    """Logs the user out by invalidating the active session token."""
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        revoke_session(token)
    return {"success": True, "message": "Logged out successfully."}


@app.get("/token", summary="Token validation")
@app.post("/token", summary="Token validation")
async def check_token(authorization: Optional[str] = Header(None)):
    """Validates session token authenticity."""
    user = get_current_user_optional(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return {"valid": True, "user": user}


@app.get("/session-info", summary="Retrieve User Session Information")
@app.get("/session-data", summary="Retrieve User Session Data")
async def session_info(authorization: Optional[str] = Header(None)):
    """Retrieves user-specific session data for personalized AI interaction."""
    user = get_current_user_optional(authorization)
    if not user:
        return {"success": False, "user": None, "message": "Guest session active."}
    return {"success": True, "user": user}


# --- Recommendation History ---

@app.get("/history", summary="User Recommendation History")
async def history(authorization: Optional[str] = Header(None)):
    """Displays a log of the user's past recommendation queries and results."""
    user = get_current_user_optional(authorization)
    user_email = user["email"] if user else None
    return get_user_history(user_email=user_email)


# --- AI Planner Endpoints ---

@app.post("/generate-home", summary="Generate Home Interior Budget Plan")
async def api_generate_home(
    payload: HomePlanRequest,
    authorization: Optional[str] = Header(None)
):
    """Accepts home-related preferences and budget to return tailored product suggestions."""
    user = get_current_user_optional(authorization)
    user_email = user["email"] if user else "guest@pocketsmart.ai"
    
    plan_data = generate_home_plan(
        room_type=payload.room_type,
        style_preference=payload.style_preference,
        budget=payload.budget,
        currency=payload.currency or "$",
        space_size=payload.space_size or "Standard (14x18 ft)",
        custom_notes=payload.custom_notes or ""
    )
    
    save_recommendation_history(
        user_email=user_email,
        plan_type="Home Interior",
        title=f"{payload.style_preference} {payload.room_type}",
        budget=payload.budget,
        currency=payload.currency or "$",
        summary=f"{len(plan_data.get('products', []))} products curated within budget.",
        details=plan_data
    )
    return plan_data


@app.post("/generate-party", summary="Generate Party & Event Budget Plan")
async def api_generate_party(
    payload: PartyPlanRequest,
    authorization: Optional[str] = Header(None)
):
    """Processes party details and guest count to recommend venue, food, and decoration items."""
    user = get_current_user_optional(authorization)
    user_email = user["email"] if user else "guest@pocketsmart.ai"
    
    plan_data = generate_party_plan(
        event_type=payload.event_type,
        guest_count=payload.guest_count,
        budget=payload.budget,
        currency=payload.currency or "$",
        theme_preference=payload.theme_preference or "Modern Neon & Cocktail Loft",
        custom_notes=payload.custom_notes or ""
    )
    
    save_recommendation_history(
        user_email=user_email,
        plan_type="Party Planner",
        title=f"{payload.event_type} ({payload.guest_count} Guests)",
        budget=payload.budget,
        currency=payload.currency or "$",
        summary=f"Venue + Catering + Decor allocated at {payload.currency or '$'}{plan_data.get('cost_per_guest', 0)}/guest.",
        details=plan_data
    )
    return plan_data


@app.post("/generate-jewelry", summary="Generate Jewelry & Styling Recommendations")
async def api_generate_jewelry(
    payload: JewelryPlanRequest,
    authorization: Optional[str] = Header(None)
):
    """Uses text and optional image inputs to suggest jewelry based on outfit and occasion."""
    user = get_current_user_optional(authorization)
    user_email = user["email"] if user else "guest@pocketsmart.ai"
    
    plan_data = generate_jewelry_plan(
        occasion=payload.occasion,
        outfit_style=payload.outfit_style,
        metal_preference=payload.metal_preference,
        budget=payload.budget,
        currency=payload.currency or "$",
        image_base64=payload.image_base64,
        image_mime_type=payload.image_mime_type or "image/jpeg",
        custom_notes=payload.custom_notes or ""
    )
    
    save_recommendation_history(
        user_email=user_email,
        plan_type="Jewelry Studio",
        title=f"{payload.occasion} ({payload.metal_preference})",
        budget=payload.budget,
        currency=payload.currency or "$",
        summary=f"{len(plan_data.get('recommendations', []))} matching pieces curated.",
        details=plan_data
    )
    return plan_data


@app.post("/generate-travel", summary="Generate Travel & Vacation Budget Plan")
async def api_generate_travel(
    payload: TravelPlanRequest,
    authorization: Optional[str] = Header(None)
):
    """Generates optimized travel budget allocation across flights, lodging, dining, and excursions."""
    user = get_current_user_optional(authorization)
    user_email = user["email"] if user else "guest@pocketsmart.ai"
    
    plan_data = generate_travel_plan(
        destination=payload.destination,
        duration_days=payload.duration_days,
        travelers_count=payload.travelers_count,
        budget=payload.budget,
        currency=payload.currency or "$",
        travel_style=payload.travel_style or "Boutique Adventure",
        custom_notes=payload.custom_notes or ""
    )
    
    save_recommendation_history(
        user_email=user_email,
        plan_type="Travel Planner",
        title=f"{payload.destination} ({payload.duration_days} Days)",
        budget=payload.budget,
        currency=payload.currency or "$",
        summary=f"Daily burn rate: {payload.currency or '$'}{plan_data.get('daily_burn_rate', 0)}/day across {payload.travelers_count} traveler(s).",
        details=plan_data
    )
    return plan_data


@app.post("/generate-tech", summary="Generate Tech Workstation Hardware Plan")
async def api_generate_tech(
    payload: TechPlanRequest,
    authorization: Optional[str] = Header(None)
):
    """Generates workstation and tech hardware gear recommendations maximizing price-to-performance ratio."""
    user = get_current_user_optional(authorization)
    user_email = user["email"] if user else "guest@pocketsmart.ai"
    
    plan_data = generate_tech_plan(
        workflow_type=payload.workflow_type,
        form_factor=payload.form_factor,
        budget=payload.budget,
        currency=payload.currency or "$",
        custom_notes=payload.custom_notes or ""
    )
    
    save_recommendation_history(
        user_email=user_email,
        plan_type="Tech Workstation",
        title=f"{payload.workflow_type} Setup",
        budget=payload.budget,
        currency=payload.currency or "$",
        summary=f"{len(plan_data.get('hardware_items', []))} hardware components curated.",
        details=plan_data
    )
    return plan_data


@app.post("/generate-wedding", summary="Generate Wedding Celebration Capital Plan")
async def api_generate_wedding(
    payload: WeddingPlanRequest,
    authorization: Optional[str] = Header(None)
):
    """Generates milestone wedding budget allocations avoiding typical industry vendor markup."""
    user = get_current_user_optional(authorization)
    user_email = user["email"] if user else "guest@pocketsmart.ai"
    
    plan_data = generate_wedding_plan(
        event_scale=payload.event_scale,
        guest_count=payload.guest_count,
        budget=payload.budget,
        currency=payload.currency or "$",
        cultural_theme=payload.cultural_theme or "Contemporary Fusion",
        custom_notes=payload.custom_notes or ""
    )
    
    save_recommendation_history(
        user_email=user_email,
        plan_type="Wedding Capital",
        title=f"{payload.cultural_theme} Wedding ({payload.guest_count} Guests)",
        budget=payload.budget,
        currency=payload.currency or "$",
        summary=f"Cost per guest: {payload.currency or '$'}{plan_data.get('cost_per_guest', 0)}.",
        details=plan_data
    )
    return plan_data


@app.post("/generate-grocery", summary="Generate Weekly Grocery & Nutrition Meal Plan")
async def api_generate_grocery(
    payload: GroceryPlanRequest,
    authorization: Optional[str] = Header(None)
):
    """Generates high-nutrition, low-waste grocery and meal prep plans."""
    user = get_current_user_optional(authorization)
    user_email = user["email"] if user else "guest@pocketsmart.ai"
    
    plan_data = generate_grocery_plan(
        household_size=payload.household_size,
        dietary_regime=payload.dietary_regime,
        weekly_budget=payload.weekly_budget,
        currency=payload.currency or "$",
        custom_notes=payload.custom_notes or ""
    )
    
    save_recommendation_history(
        user_email=user_email,
        plan_type="Grocery Blueprint",
        title=f"{payload.dietary_regime} ({payload.household_size} Persons)",
        budget=payload.weekly_budget,
        currency=payload.currency or "$",
        summary=f"Cost per meal: {payload.currency or '$'}{plan_data.get('cost_per_meal', 0)}/meal.",
        details=plan_data
    )
    return plan_data


@app.post("/generate-student", summary="Generate Collegiate Student Living Budget")
async def api_generate_student(
    payload: StudentPlanRequest,
    authorization: Optional[str] = Header(None)
):
    """Generates undergraduate / graduate monthly student survival and lifestyle budget allocation."""
    user = get_current_user_optional(authorization)
    user_email = user["email"] if user else "guest@pocketsmart.ai"
    
    plan_data = generate_student_plan(
        academic_level=payload.academic_level,
        monthly_allowance=payload.monthly_allowance,
        currency=payload.currency or "$",
        city_tier=payload.city_tier or "Metropolitan Hub",
        custom_notes=payload.custom_notes or ""
    )
    
    save_recommendation_history(
        user_email=user_email,
        plan_type="Collegiate Budget",
        title=f"{payload.academic_level} Living Plan",
        budget=payload.monthly_allowance,
        currency=payload.currency or "$",
        summary=f"Daily discretionary: {payload.currency or '$'}{plan_data.get('daily_discretionary', 0)}/day.",
        details=plan_data
    )
    return plan_data


if __name__ == "__main__":
    print("[PocketSmart AI] Starting Backend Server on http://127.0.0.1:8000")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
