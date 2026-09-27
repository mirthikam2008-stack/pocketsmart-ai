"""
FastAPI Test Verification Suite for PocketSmart AI (8 Real-World Optimizers)
"""

from fastapi.testclient import TestClient
from backend.main import app

def run_suite():
    with TestClient(app) as client:
        # 1. Startup
        res = client.get("/startup")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "operational"
        assert len(data["services_loaded"]) >= 8
        print("[PASS] /startup verified (All 8 Optimizers Active)")

        # 2. Homepage HTML
        res = client.get("/")
        assert res.status_code == 200
        assert "PocketSmart" in res.text
        print("[PASS] / (HTML UI) verified")

        # 3. Auth and Session flow
        email = "demo@pocketsmart.ai"
        login_res = client.post("/login", json={"email": email, "password": "DemoPass123!"})
        assert login_res.status_code == 200
        data = login_res.json()
        assert data["success"] is True
        token = data["token"]
        print("[PASS] /login verified")

        # Session info
        session_res = client.get("/session-info", headers={"Authorization": f"Bearer {token}"})
        assert session_res.status_code == 200
        assert session_res.json()["success"] is True
        print("[PASS] /session-info verified")

        # Session data
        sdata_res = client.get("/session-data", headers={"Authorization": f"Bearer {token}"})
        assert sdata_res.status_code == 200
        print("[PASS] /session-data verified")

        # Token validation
        tok_res = client.get("/token", headers={"Authorization": f"Bearer {token}"})
        assert tok_res.status_code == 200
        print("[PASS] /token verified")

        # 4. All 8 Planner Endpoints
        # 1. Home Planner
        home_payload = {
            "room_type": "Living Room",
            "style_preference": "Modern Minimalist",
            "budget": 750.0,
            "currency": "$",
            "space_size": "Standard (14x18 ft)",
            "custom_notes": "Include compact sofa"
        }
        h_res = client.post("/generate-home", json=home_payload, headers={"Authorization": f"Bearer {token}"})
        assert h_res.status_code == 200
        assert "products" in h_res.json()
        print("[PASS] /generate-home verified")

        # 2. Party Planner
        party_payload = {
            "event_type": "Birthday Celebration",
            "guest_count": 25,
            "budget": 800.0,
            "currency": "$",
            "theme_preference": "Modern Neon",
            "custom_notes": "Rooftop venue"
        }
        p_res = client.post("/generate-party", json=party_payload, headers={"Authorization": f"Bearer {token}"})
        assert p_res.status_code == 200
        assert "venue_suggestions" in p_res.json()
        print("[PASS] /generate-party verified")

        # 3. Jewelry Planner
        jewel_payload = {
            "occasion": "Wedding",
            "outfit_style": "Emerald Silk Gown",
            "metal_preference": "22K Gold Finish",
            "budget": 500.0,
            "currency": "$",
            "custom_notes": "Choker set"
        }
        j_res = client.post("/generate-jewelry", json=jewel_payload, headers={"Authorization": f"Bearer {token}"})
        assert j_res.status_code == 200
        assert "recommendations" in j_res.json()
        print("[PASS] /generate-jewelry verified")

        # 4. Travel Planner
        travel_payload = {
            "destination": "Bali, Indonesia",
            "duration_days": 7,
            "travelers_count": 2,
            "budget": 1200.0,
            "currency": "$",
            "travel_style": "Boutique Adventure"
        }
        tr_res = client.post("/generate-travel", json=travel_payload, headers={"Authorization": f"Bearer {token}"})
        assert tr_res.status_code == 200
        assert "flights_transport" in tr_res.json()
        print("[PASS] /generate-travel verified")

        # 5. Tech Workstation Planner
        tech_payload = {
            "workflow_type": "Full-Stack & AI Engineering",
            "form_factor": "Laptop + 4K USB-C Hub Display",
            "budget": 1800.0,
            "currency": "$"
        }
        tc_res = client.post("/generate-tech", json=tech_payload, headers={"Authorization": f"Bearer {token}"})
        assert tc_res.status_code == 200
        assert "hardware_items" in tc_res.json()
        print("[PASS] /generate-tech verified")

        # 6. Milestone Wedding Planner
        wed_payload = {
            "event_scale": "Intimate Boutique Wedding (50-100 Guests)",
            "guest_count": 80,
            "budget": 4500.0,
            "currency": "$",
            "cultural_theme": "Royal Heritage"
        }
        wd_res = client.post("/generate-wedding", json=wed_payload, headers={"Authorization": f"Bearer {token}"})
        assert wd_res.status_code == 200
        assert "venue_decor" in wd_res.json()
        print("[PASS] /generate-wedding verified")

        # 7. Weekly Grocery Planner
        groc_payload = {
            "household_size": 2,
            "dietary_regime": "High-Protein Mediterranean",
            "weekly_budget": 150.0,
            "currency": "$"
        }
        gr_res = client.post("/generate-grocery", json=groc_payload, headers={"Authorization": f"Bearer {token}"})
        assert gr_res.status_code == 200
        assert "grocery_items" in gr_res.json()
        print("[PASS] /generate-grocery verified")

        # 8. Collegiate Student Planner
        stud_payload = {
            "academic_level": "Undergraduate Student (B.S.)",
            "monthly_allowance": 600.0,
            "currency": "$",
            "city_tier": "High-Cost Metropolitan Campus"
        }
        st_res = client.post("/generate-student", json=stud_payload, headers={"Authorization": f"Bearer {token}"})
        assert st_res.status_code == 200
        assert "allocation_categories" in st_res.json()
        print("[PASS] /generate-student verified")

        # History
        hist_res = client.get("/history", headers={"Authorization": f"Bearer {token}"})
        assert hist_res.status_code == 200
        assert isinstance(hist_res.json(), list)
        print("[PASS] /history verified")

        # Logout
        logout_res = client.post("/logout", headers={"Authorization": f"Bearer {token}"})
        assert logout_res.status_code == 200
        print("[PASS] /logout verified")

        print("\nALL 8 REAL-WORLD FASTAPI OPTIMIZERS & ENDPOINTS PASSED 100% VERIFICATION!")

if __name__ == "__main__":
    run_suite()
