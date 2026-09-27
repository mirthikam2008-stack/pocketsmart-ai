"""
PocketSmart AI - Specialized Planner Service
Handles AI generation for:
1. Home Interior Budget Planner (/generate-home)
2. Party Budget Planner (/generate-party)
3. Jewelry Budget Planner (/generate-jewelry) with multimodal image support
"""

import os
import json
import base64
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

FALLBACK_HOME_PLANS = {
    "Living Room": [
        {
            "id": "h-101",
            "name": "Nordic Minimalist 3-Seater Sofa",
            "category": "Furniture",
            "store": "IKEA",
            "price": 349.99,
            "currency": "$",
            "rating": 4.8,
            "image": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=600&q=80",
            "description": "High resilience foam cushion with stain-resistant tailored weave fabric.",
            "link": "https://www.ikea.com",
            "platform": "IKEA",
            "saving_tip": "Look for flat-pack self-pickup for an additional $40 saving."
        },
        {
            "id": "h-102",
            "name": "Solid Oak Scandi Coffee Table with Storage",
            "category": "Furniture",
            "store": "Wayfair",
            "price": 129.50,
            "currency": "$",
            "rating": 4.7,
            "image": "https://images.unsplash.com/photo-1533090161767-e6ffed986c88?auto=format&fit=crop&w=600&q=80",
            "description": "Minimalist silhouette featuring hidden slide-out drawer.",
            "link": "https://www.wayfair.com",
            "platform": "Wayfair",
            "saving_tip": "Apply promotional coupon code at checkout."
        },
        {
            "id": "h-103",
            "name": "Dimmable Matte Black Floor Arc Lamp",
            "category": "Lighting",
            "store": "Amazon Home",
            "price": 64.99,
            "currency": "$",
            "rating": 4.9,
            "image": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=600&q=80",
            "description": "Warm-tone 2700K energy-saving LED bulb with marble base.",
            "link": "https://www.amazon.com",
            "platform": "Amazon",
            "saving_tip": "Check for Amazon Warehouse open-box deals for 20% off."
        },
        {
            "id": "h-104",
            "name": "Handwoven Geometric Jute Area Rug (5x7 ft)",
            "category": "Decor",
            "store": "Target",
            "price": 89.00,
            "currency": "$",
            "rating": 4.6,
            "image": "https://images.unsplash.com/photo-1600121848594-d8644e57abab?auto=format&fit=crop&w=600&q=80",
            "description": "Eco-friendly sustainable natural jute fiber with non-slip backing.",
            "link": "https://www.target.com",
            "platform": "Target",
            "saving_tip": "Target RedCard holders get an extra 5% instant discount."
        }
    ]
}

FALLBACK_TRAVEL_PLANS = {
    "Bali & Southeast Asia": {
        "destination": "Bali, Indonesia (7-Day Island Getaway)",
        "flights_transport": [
            {"item": "Roundtrip Economy Flights with Baggage", "estimated_cost": 420.0, "provider": "Skyscanner / Airline Direct", "saving_hack": "Booking 6 weeks prior on Tuesday saves up to 24%."},
            {"item": "Private Airport & Scooter Rental (7 Days)", "estimated_cost": 65.0, "provider": "Local Certified Rentals", "saving_hack": "Weekly bulk scooter rental saves 40% vs daily hailing."}
        ],
        "accommodation": [
            {"item": "Boutique Eco-Villa with Private Pool (Ubud/Seminyak)", "estimated_cost": 310.0, "provider": "Agoda / Airbnb Superhost", "saving_hack": "Direct WhatsApp booking with villa owner often waives platform fees."}
        ],
        "food_activities": [
            {"item": "Artisanal Warung & Beach Club Dining Package", "estimated_cost": 180.0, "provider": "Curated Local Eateries", "saving_hack": "Indulge in authentic local Warungs for lunch and beach clubs for sunset drinks."},
            {"item": "Nusa Penida Snorkel Tour & Sacred Temple Passes", "estimated_cost": 75.0, "provider": "GetYourGuide / Local Guides", "saving_hack": "Group booking saves $30 compared to private tours."}
        ]
    }
}

FALLBACK_TECH_PLANS = [
    {
        "item_name": "Apple MacBook Air M3 (16GB RAM / 512GB SSD)",
        "category": "Core Workstation",
        "retailer": "Apple / Amazon Renewed / B&H",
        "price": 999.0,
        "rating": 4.9,
        "image": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=600&q=80",
        "description": "Silent fanless architecture with 18-hour battery longevity for demanding professional multitasking.",
        "saving_tip": "Apple Education Store or Certified Refurbished saves an instant $150 with full 1-year warranty."
    },
    {
        "item_name": "Dell UltraSharp 27-inch 4K USB-C Hub Monitor",
        "category": "Display & Ergonomics",
        "retailer": "Dell Direct / Amazon",
        "price": 380.0,
        "rating": 4.8,
        "image": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=600&q=80",
        "description": "90W USB-C single cable charging, 98% DCI-P3 color accuracy with IPS Black technology.",
        "saving_tip": "Look for manufacturer open-box deals on Dell Outlet for 25% discount."
    },
    {
        "item_name": "Logitech MX Master 3S + MX Keys S Combo",
        "category": "Peripherals",
        "retailer": "Logitech / Best Buy",
        "price": 175.0,
        "rating": 4.9,
        "image": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=600&q=80",
        "description": "Quiet-click electromagnetic scroll wheel with multi-device cross-computer flow.",
        "saving_tip": "Bundle package deal saves $30 over purchasing keyboard and mouse separately."
    },
    {
        "item_name": "Autonomous SmartDesk 2 Dual-Motor Standing Desk Frame",
        "category": "Ergonomics",
        "retailer": "Autonomous / IKEA Top",
        "price": 240.0,
        "rating": 4.7,
        "image": "https://images.unsplash.com/photo-1595428774223-ef52624120d2?auto=format&fit=crop&w=600&q=80",
        "description": "Dual electric motors with 4 programmable height presets and anti-collision sensor.",
        "saving_tip": "Buy motorized frame only and pair with an IKEA Karlby countertop to save $200."
    }
]

FALLBACK_WEDDING_PLANS = {
    "Ceremony & Reception": {
        "venue_decor": [
            {"category": "Heritage Lawn / Banquet Hall Leasing", "estimated_cost": 1500.0, "saving_hack": "Weekday or morning ceremony slots save up to 40% on rental fees."},
            {"category": "Floral Mandap / Altar & Ambient Fairy Lighting", "estimated_cost": 650.0, "saving_hack": "Incorporate seasonal marigolds, greenery, and reusable LED drape fixtures."}
        ],
        "catering_hospitality": [
            {"category": "Multi-Course Gourmet Buffet (150 Guests)", "estimated_cost": 1800.0, "saving_hack": "Opt for live chaat/tapas stations rather than costly individual sit-down courses."},
            {"category": "Signature Mocktail & Beverage Bar", "estimated_cost": 350.0, "saving_hack": "Supply your own craft syrups and mixers with a flat bartender service fee."}
        ],
        "photography_makeup": [
            {"category": "Cinematic 2-Day Photo & 4K Teaser Video", "estimated_cost": 850.0, "saving_hack": "Hire emerging talented boutique wedding photographers instead of commercial agencies."},
            {"category": "Bridal HD Airbrush & Family Styling", "estimated_cost": 350.0, "saving_hack": "Book bundled hair and makeup packages for bride and bridesmaids."}
        ]
    }
}

FALLBACK_GROCERY_PLANS = {
    "Balanced Nutrition Blueprint": [
        {"item": "Farm-Fresh Whole Produce (Greens, Tomatoes, Berries, Root Veggies)", "cost": 45.0, "store": "Local Farmers Market / Costco Wholesale", "tip": "Buy seasonal bulk produce and flash-freeze portions."},
        {"item": "High-Density Protein Matrix (Eggs, Greek Yogurt, Chicken Breast/Tofu)", "cost": 55.0, "store": "Trader Joe's / Local Butcher", "tip": "Eggs and lentils provide top protein-per-dollar efficiency."},
        {"item": "Complex Carbohydrates & Grains (Oats, Quinoa, Brown Rice, Sourdough)", "cost": 25.0, "store": "Aldi / Supermarket Bulk Bin", "tip": "Bulk dried grains cost 70% less than pre-packaged boxed carbs."},
        {"item": "Healthy Fats & Pantry Staples (Extra Virgin Olive Oil, Almonds, Chia Seeds)", "cost": 35.0, "store": "Target / Amazon Pantry", "tip": "Buy cold-pressed oils in tins rather than expensive mini bottles."}
    ]
}

FALLBACK_STUDENT_PLANS = {
    "Semester Survival Allocation": [
        {"category": "Digital Textbooks & Research Tools", "estimated_cost": 80.0, "hack": "Rent digital e-textbooks or check university open-access library repositories."},
        {"category": "Campus Meal Card / Batch Meal Prep", "estimated_cost": 220.0, "hack": "Prep Sunday lunches in bulk to eliminate daily $15 campus cafeteria overhead."},
        {"category": "Public Transit Semester Pass", "estimated_cost": 60.0, "hack": "Avail 50% subsidized university student transit discount."},
        {"category": "Shared Room Utilities & High-Speed Fiber", "estimated_cost": 90.0, "hack": "Split split-tier internet bills across roommates."}
    ]
}

FALLBACK_PARTY_PLANS = {
    "Birthday": {
        "venue_suggestions": [
            {
                "title": "Skyline Garden Terrace Loft",
                "type": "Outdoor & Rooftop",
                "estimated_cost": 450.00,
                "capacity": "30-50 guests",
                "perks": ["Ambient fairy lights", "Bluetooth sound system", "BYO beverage allowed"],
                "saving_hack": "Booking Sunday afternoon saves up to 35% compared to Saturday night."
            },
            {
                "title": "Boutique Community Club Hall",
                "type": "Indoor Hall",
                "estimated_cost": 220.00,
                "capacity": "20-40 guests",
                "perks": ["Chairs & tables included", "Air conditioned", "Kitchen access"],
                "saving_hack": "Inquire for resident member discounts."
            }
        ],
        "food_catering": [
            {
                "item": "Gourmet Slider & Artisan Finger Food Buffet",
                "estimated_cost": 320.00,
                "servings": "30 guests",
                "provider_type": "Local Catering / Prep",
                "details": "Mini pulled jackfruit & chicken sliders, loaded waffle fries, fresh dips and skewers."
            },
            {
                "item": "Signature Tiered Custom Cake & Cupcake Bar",
                "estimated_cost": 110.00,
                "servings": "30 guests",
                "provider_type": "Home Baker Specialist",
                "details": "Semi-naked vanilla bean cake with edible gold foil & 24 matching cupcakes."
            },
            {
                "item": "Artisanal Mocktail & Spritzer Station",
                "estimated_cost": 85.00,
                "servings": "30 guests",
                "provider_type": "DIY Beverage Bar",
                "details": "Sparkling berry smash, citrus lavender cooler, fresh mint & dispensers."
            }
        ],
        "decorations": [
            {
                "item": "Custom Organic Balloon Arch & Shimmer Wall Backdrop",
                "estimated_cost": 75.00,
                "type": "Backdrop & Photo Booth",
                "saving_tip": "Buy balloon kit online and assemble with electric pump to save $150 on setup."
            },
            {
                "item": "LED Neon 'Happy Birthday' Sign + Fairy Lights",
                "estimated_cost": 45.00,
                "type": "Lighting & Ambience",
                "saving_tip": "Reusable USB powered sign can be rented or reused."
            },
            {
                "item": "Eco-friendly Table Linens & Ceramic Tableware Set",
                "estimated_cost": 50.00,
                "type": "Table Styling",
                "saving_tip": "Opt for rental sets instead of disposable plastic."
            }
        ]
    }
}

FALLBACK_JEWELRY_PLANS = [
    {
        "piece_name": "Royal Kundan & Polki Choker Necklace Set",
        "metal_type": "22K Gold Plated Brass with Semi-Precious Stones",
        "estimated_price": 145.00,
        "matching_score": "98% Match",
        "image": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=600&q=80",
        "occasion_fit": "Wedding / Reception / Festive Sangeet",
        "outfit_pairing": "Pairs exquisitely with deep emerald green, ruby red, or royal navy silk and velvet ensembles.",
        "retailer": "Tanishq / CaratLane / Curated Artisans",
        "gemstone": "Emerald drops, lustrous faux pearls, uncut Polki finish",
        "smart_buyer_tip": "Choose 22K micron electroplated silver-alloy base to get the authentic heirloom look at 1/10th the cost of solid gold."
    },
    {
        "piece_name": "Art Deco Solitaire Teardrop Diamond-Cut Earrings",
        "metal_type": "18K White Gold / 925 Sterling Silver",
        "estimated_price": 95.00,
        "matching_score": "95% Match",
        "image": "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=600&q=80",
        "occasion_fit": "Cocktail Party / Evening Gala / Reception",
        "outfit_pairing": "Complements modern gowns, satin dresses, and contemporary Indo-western outfits.",
        "retailer": "BlueStone / Swarovski / Amazon Premium",
        "gemstone": "Moissanite VVS1 Clarity / Lab-Grown Brilliant Cut",
        "smart_buyer_tip": "Moissanite tests positive on diamond selectors and gives 2.4x more fire at a fraction of diamond prices."
    },
    {
        "piece_name": "Filigree Floral Statement Cuff Bracelet",
        "metal_type": "Rose Gold & Antique Silver Tone",
        "estimated_price": 60.00,
        "matching_score": "92% Match",
        "image": "https://images.unsplash.com/photo-1611591475886-df418c35f8be?auto=format&fit=crop&w=600&q=80",
        "occasion_fit": "Festival / Anniversary / Dinner Date",
        "outfit_pairing": "Accents pastel lehengas, fusion jumpsuits, or formal evening sarees.",
        "retailer": "GIVA / Melorra",
        "gemstone": "Zirconia accents with matte polish",
        "smart_buyer_tip": "Adjustable open-cuff design ensures zero resizing fees."
    }
]


def generate_home_plan(
    room_type: str,
    style_preference: str,
    budget: float,
    currency: str = "$",
    space_size: str = "Medium",
    custom_notes: str = "",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Generates budget-optimized home interior product suggestions."""
    try:
        from services.gemini_service import get_gemini_client
        client = get_gemini_client(api_key=api_key)
        
        prompt = f"""
You are PocketSmart AI's Senior Interior Designer & Budget Procurement Specialist.
Generate a structured, budget-optimized home interior design plan.

Parameters:
- Room Type: {room_type}
- Style Preference: {style_preference}
- Total Budget: {currency}{budget:,.2f}
- Space Dimensions/Size: {space_size}
- Additional User Notes: {custom_notes}

Respond strictly in valid JSON format matching this schema:
{{
  "room_type": "{room_type}",
  "style": "{style_preference}",
  "total_budget": {budget},
  "allocated_budget": 0.0,
  "savings_achieved": 0.0,
  "currency": "{currency}",
  "design_concept_summary": "High-level summary of the interior vibe and color palette",
  "styling_rules": ["Tip 1", "Tip 2", "Tip 3"],
  "budget_breakdown": {{
    "furniture_pct": 55,
    "lighting_pct": 15,
    "decor_and_rugs_pct": 20,
    "contingency_pct": 10
  }},
  "products": [
    {{
      "id": "h-01",
      "name": "Product Name",
      "category": "Furniture | Lighting | Rugs | Wall Art | Storage",
      "store": "IKEA | Amazon | Wayfair | Target | West Elm",
      "price": 120.0,
      "rating": 4.8,
      "image": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=600&q=80",
      "description": "Why this item fits the space and budget",
      "link": "https://www.google.com/search?q=buy+item",
      "platform": "IKEA",
      "saving_tip": "Actionable buying tip to save money"
    }}
  ]
}}
Ensure the total sum of product prices fits neatly within the budget of {currency}{budget:,.2f}.
Include 4-6 diverse items across furniture, lighting, and decor.
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text)
        return data
    except Exception as e:
        items = list(FALLBACK_HOME_PLANS.get("Living Room", []))
        total_items_cost = sum(item["price"] for item in items)
        scale = (budget * 0.85) / max(total_items_cost, 1.0)
        
        scaled_products = []
        for idx, item in enumerate(items):
            p = dict(item)
            p["price"] = round(item["price"] * scale, 2)
            p["currency"] = currency
            scaled_products.append(p)
            
        allocated = sum(p["price"] for p in scaled_products)
        return {
            "room_type": room_type,
            "style": style_preference,
            "total_budget": budget,
            "allocated_budget": round(allocated, 2),
            "savings_achieved": round(max(budget - allocated, 0), 2),
            "currency": currency,
            "design_concept_summary": f"A cohesive {style_preference} aesthetic curated for {room_type}, maximizing natural light, ergonomic balance, and multi-functional high-value accents.",
            "styling_rules": [
                f"Keep 60% neutral primary tones, 30% secondary textures, and 10% bold {style_preference} accents.",
                "Utilize multi-level lighting (ambient, task, accent) rather than a single harsh overhead fixture.",
                "Position main seating opposite natural light entryways for maximum spatial illusion."
            ],
            "budget_breakdown": {
                "furniture_pct": 55,
                "lighting_pct": 15,
                "decor_and_rugs_pct": 20,
                "contingency_pct": 10
            },
            "products": scaled_products
        }


def generate_party_plan(
    event_type: str,
    guest_count: int,
    budget: float,
    currency: str = "$",
    theme_preference: str = "Modern Elegance",
    custom_notes: str = "",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Generates event, catering, venue, and decoration budget allocation."""
    try:
        from services.gemini_service import get_gemini_client
        client = get_gemini_client(api_key=api_key)
        
        prompt = f"""
You are PocketSmart AI's Master Event Planner and Budget Optimizer.
Create a comprehensive party budget plan.

Parameters:
- Event Type: {event_type}
- Number of Guests: {guest_count}
- Total Budget: {currency}{budget:,.2f}
- Theme: {theme_preference}
- Special Notes: {custom_notes}

Respond strictly in valid JSON format matching this schema:
{{
  "event_type": "{event_type}",
  "guest_count": {guest_count},
  "total_budget": {budget},
  "allocated_budget": 0.0,
  "cost_per_guest": 0.0,
  "currency": "{currency}",
  "theme_summary": "Description of the party vibe and aesthetic",
  "smart_organizer_tips": ["Hack 1", "Hack 2", "Hack 3"],
  "venue_suggestions": [
    {{
      "title": "Venue Option",
      "type": "Outdoor / Banquet / Rooftop / Community Hall",
      "estimated_cost": 300.0,
      "capacity": "{guest_count} guests",
      "perks": ["Perk 1", "Perk 2"],
      "saving_hack": "How to save money on this venue"
    }}
  ],
  "food_catering": [
    {{
      "item": "Menu Package / Dish",
      "estimated_cost": 250.0,
      "servings": "{guest_count} guests",
      "provider_type": "Buffet / Food Truck / Finger Foods",
      "details": "Description of the menu"
    }}
  ],
  "decorations": [
    {{
      "item": "Decor Element",
      "estimated_cost": 80.0,
      "type": "Backdrop / Centerpiece / Mood Lighting",
      "saving_tip": "DIY or rental optimization tip"
    }}
  ]
}}
Ensure the entire plan strictly adheres to {currency}{budget:,.2f}.
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        base = FALLBACK_PARTY_PLANS["Birthday"]
        cost_per_person = budget / max(guest_count, 1)
        allocated = budget * 0.92
        return {
            "event_type": event_type,
            "guest_count": guest_count,
            "total_budget": budget,
            "allocated_budget": round(allocated, 2),
            "cost_per_guest": round(cost_per_person, 2),
            "currency": currency,
            "theme_summary": f"A vibrant and stylish {theme_preference} celebration designed to delight {guest_count} guests with high hospitality impact and minimal overhead.",
            "smart_organizer_tips": [
                "Serve high-energy grazing platters & signature punch bowls rather than expensive plated courses.",
                "Opt for digital animated invites to eliminate printing & postal overhead.",
                "Create a dedicated Instagrammable photo-wall corner to naturally elevate the guest experience."
            ],
            "venue_suggestions": base["venue_suggestions"],
            "food_catering": base["food_catering"],
            "decorations": base["decorations"]
        }


def generate_jewelry_plan(
    occasion: str,
    outfit_style: str,
    metal_preference: str,
    budget: float,
    currency: str = "$",
    image_base64: Optional[str] = None,
    image_mime_type: Optional[str] = "image/jpeg",
    custom_notes: str = "",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Generates personalized jewelry pairings with optional image/vision intelligence."""
    try:
        from services.gemini_service import get_gemini_client
        client = get_gemini_client(api_key=api_key)
        
        prompt = f"""
You are PocketSmart AI's Haute Joaillerie & Personal Jewelry Stylist.
Analyze the user's outfit, occasion, metal preferences, and budget to curate matching jewelry recommendations.

Parameters:
- Occasion: {occasion}
- Outfit Style / Color / Cut: {outfit_style}
- Metal Preference: {metal_preference}
- Total Budget: {currency}{budget:,.2f}
- Custom Styling Notes: {custom_notes}

Respond strictly in valid JSON format matching this schema:
{{
  "occasion": "{occasion}",
  "outfit_style": "{outfit_style}",
  "metal_preference": "{metal_preference}",
  "total_budget": {budget},
  "allocated_budget": 0.0,
  "currency": "{currency}",
  "styling_verdict": "Expert assessment of neckline, silhouette, color contrast, and jewelry balance",
  "color_harmony_notes": "Specific color matching rules for the selected outfit",
  "recommendations": [
    {{
      "piece_name": "Jewelry Piece Title",
      "category": "Necklace / Choker | Earrings | Bracelet / Bangles | Ring | Maang Tikka",
      "metal_type": "{metal_preference} / Plated Silver / 18K Vermeil",
      "estimated_price": 120.0,
      "matching_score": "96% Match",
      "image": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=600&q=80",
      "occasion_fit": "Why this fits {occasion}",
      "outfit_pairing": "How to wear it with {outfit_style}",
      "retailer": "Tanishq / CaratLane / Swarovski / GIVA / BlueStone",
      "gemstone": "Cubic Zirconia / Emerald / Pearl / Moissanite / Lab Diamond",
      "smart_buyer_tip": "Insider jewelry procurement trick to save money"
    }}
  ]
}}
Provide 3-4 complementary jewelry pieces whose sum stays within {currency}{budget:,.2f}.
"""
        contents = [prompt]
        if image_base64:
            from google.genai import types
            image_bytes = base64.b64decode(image_base64)
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime_type or "image/jpeg"))
            
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        items = list(FALLBACK_JEWELRY_PLANS)
        total_price = sum(item["estimated_price"] for item in items)
        scale = (budget * 0.9) / max(total_price, 1.0)
        
        scaled_recs = []
        for it in items:
            copy_it = dict(it)
            copy_it["estimated_price"] = round(it["estimated_price"] * scale, 2)
            copy_it["currency"] = currency
            scaled_recs.append(copy_it)
            
        allocated = sum(it["estimated_price"] for it in scaled_recs)
        return {
            "occasion": occasion,
            "outfit_style": outfit_style,
            "metal_preference": metal_preference,
            "total_budget": budget,
            "allocated_budget": round(allocated, 2),
            "currency": currency,
            "styling_verdict": f"The chosen {outfit_style} for {occasion} pairs harmoniously with high-polish {metal_preference} accents, accentuating the neckline and bringing warm radiance to your overall silhouette.",
            "color_harmony_notes": f"For {outfit_style}, balanced contrasts with lustrous stones and clean geometric symmetry prevent visual overcrowding while looking timeless.",
            "recommendations": scaled_recs
        }


def generate_travel_plan(
    destination: str,
    duration_days: int,
    travelers_count: int,
    budget: float,
    currency: str = "$",
    travel_style: str = "Boutique Adventure",
    custom_notes: str = "",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Generates optimized travel budget allocation across flights, lodging, dining, and excursions."""
    try:
        from services.gemini_service import get_gemini_client
        client = get_gemini_client(api_key=api_key)
        
        prompt = f"""
You are PocketSmart AI's Elite Travel Strategist and Global Procurement Planner.
Create an optimized travel itinerary and financial blueprint.

Parameters:
- Destination: {destination}
- Duration: {duration_days} Days
- Travelers: {travelers_count} People
- Budget: {currency}{budget:,.2f}
- Travel Style: {travel_style}
- Notes: {custom_notes}

Respond strictly in valid JSON format:
{{
  "destination": "{destination}",
  "duration_days": {duration_days},
  "travelers_count": {travelers_count},
  "total_budget": {budget},
  "allocated_budget": 0.0,
  "daily_burn_rate": 0.0,
  "currency": "{currency}",
  "itinerary_concept": "Summary of journey experience and optimal season timing",
  "flights_transport": [
    {{"item": "Transport Option", "estimated_cost": 400.0, "provider": "Provider Name", "saving_hack": "Actionable tip to save money"}}
  ],
  "accommodation": [
    {{"item": "Lodging Concept", "estimated_cost": 300.0, "provider": "Booking platform", "saving_hack": "Negotiation / loyalty tip"}}
  ],
  "food_activities": [
    {{"item": "Dining & Excursions", "estimated_cost": 200.0, "provider": "Local partners", "saving_hack": "Local culinary hack"}}
  ],
  "pro_traveler_rules": ["Tip 1", "Tip 2", "Tip 3"]
}}
Ensure the sum of all elements strictly conforms to {currency}{budget:,.2f}.
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        base = FALLBACK_TRAVEL_PLANS.get("Bali & Southeast Asia", {})
        daily = round(budget / max(duration_days, 1), 2)
        return {
            "destination": destination,
            "duration_days": duration_days,
            "travelers_count": travelers_count,
            "total_budget": budget,
            "allocated_budget": round(budget * 0.94, 2),
            "daily_burn_rate": daily,
            "currency": currency,
            "itinerary_concept": f"A balanced {travel_style} excursion to {destination} maximizing immersive cultural encounters and boutique luxury while mitigating tourist surcharge traps.",
            "flights_transport": base.get("flights_transport", []),
            "accommodation": base.get("accommodation", []),
            "food_activities": base.get("food_activities", []),
            "pro_traveler_rules": [
                "Utilize multi-currency travel debit cards with zero foreign transaction markup fees.",
                "Reserve secondary-tier boutique eco-lodges situated 10 minutes outside core tourist strips for 45% lower nightly tariffs.",
                "Dine where educated locals congregate at peak lunch hours for authentic gourmet quality at fraction of resort costs."
            ]
        }


def generate_tech_plan(
    workflow_type: str,
    form_factor: str,
    budget: float,
    currency: str = "$",
    custom_notes: str = "",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Generates workstation and tech hardware gear recommendations maximizing price-to-performance ratio."""
    try:
        from services.gemini_service import get_gemini_client
        client = get_gemini_client(api_key=api_key)
        
        prompt = f"""
You are PocketSmart AI's Lead Hardware Architect & Tech Procurement Director.
Synthesize an optimal tech workstation setup for {workflow_type}.

Parameters:
- Primary Workflow: {workflow_type} (e.g. AI Development, Video Editing, Remote Productivity)
- Form Factor: {form_factor} (e.g. Laptop + External 4K Display, Desktop Powerhouse, Mobile Minimalist)
- Budget Ceiling: {currency}{budget:,.2f}
- Custom Requirements: {custom_notes}

Respond strictly in JSON matching:
{{
  "workflow_type": "{workflow_type}",
  "form_factor": "{form_factor}",
  "total_budget": {budget},
  "allocated_budget": 0.0,
  "currency": "{currency}",
  "architecture_summary": "High-level review of CPU/GPU/RAM specs and thermal efficiency",
  "hardware_items": [
    {{
      "item_name": "Product Name",
      "category": "Core Machine | Monitor | Peripherals | Ergonomics",
      "retailer": "Apple / Amazon / Best Buy / B&H / Dell",
      "price": 899.0,
      "rating": 4.9,
      "image": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=600&q=80",
      "description": "Why this hardware matches the workflow",
      "saving_tip": "Insider refurbishment or corporate discount trick"
    }}
  ],
  "efficiency_benchmarks": ["Spec 1", "Spec 2", "Spec 3"]
}}
Ensure the total sum strictly fits {currency}{budget:,.2f}.
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        items = list(FALLBACK_TECH_PLANS)
        total_price = sum(it["price"] for it in items)
        scale = (budget * 0.92) / max(total_price, 1.0)
        
        scaled_items = []
        for it in items:
            c = dict(it)
            c["price"] = round(it["price"] * scale, 2)
            c["currency"] = currency
            scaled_items.append(c)
            
        allocated = sum(c["price"] for c in scaled_items)
        return {
            "workflow_type": workflow_type,
            "form_factor": form_factor,
            "total_budget": budget,
            "allocated_budget": round(allocated, 2),
            "currency": currency,
            "architecture_summary": f"High price-to-performance architecture calibrated for {workflow_type}, featuring unified memory, color-accurate displays, and whisper-quiet operation.",
            "hardware_items": scaled_items,
            "efficiency_benchmarks": [
                "16GB Unified RAM ensures seamless multitasking across Docker containers and heavy IDEs.",
                "Single-cable 90W USB-C hub configuration eliminates desk cable clutter.",
                "Active dual-motor standing frame reduces musculoskeletal fatigue during 10+ hour deep work sprints."
            ]
        }


def generate_wedding_plan(
    event_scale: str,
    guest_count: int,
    budget: float,
    currency: str = "$",
    cultural_theme: str = "Contemporary Fusion",
    custom_notes: str = "",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Generates milestone wedding budget allocations avoiding typical industry vendor markup."""
    try:
        from services.gemini_service import get_gemini_client
        client = get_gemini_client(api_key=api_key)
        
        prompt = f"""
You are PocketSmart AI's Luxury Wedding Director & Capital Allocator.
Structure a wedding celebration avoiding wedding industry inflated margins.

Parameters:
- Scale: {event_scale}
- Guest Count: {guest_count}
- Total Budget: {currency}{budget:,.2f}
- Theme: {cultural_theme}
- Notes: {custom_notes}

Respond strictly in JSON matching:
{{
  "event_scale": "{event_scale}",
  "guest_count": {guest_count},
  "total_budget": {budget},
  "allocated_budget": 0.0,
  "cost_per_guest": 0.0,
  "currency": "{currency}",
  "curation_summary": "Vision statement and theme atmosphere",
  "venue_decor": [{{"category": "Venue/Decor", "estimated_cost": 1200.0, "saving_hack": "Negotiation tip"}}],
  "catering_hospitality": [{{"category": "Food/Beverage", "estimated_cost": 1500.0, "saving_hack": "Menu strategy"}}],
  "photography_makeup": [{{"category": "Media/Styling", "estimated_cost": 600.0, "saving_hack": "Talent procurement"}}],
  "wedding_financial_rules": ["Rule 1", "Rule 2", "Rule 3"]
}}
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        base = FALLBACK_WEDDING_PLANS["Ceremony & Reception"]
        cost_per_guest = round(budget / max(guest_count, 1), 2)
        return {
            "event_scale": event_scale,
            "guest_count": guest_count,
            "total_budget": budget,
            "allocated_budget": round(budget * 0.95, 2),
            "cost_per_guest": cost_per_guest,
            "currency": currency,
            "curation_summary": f"An enchanting {cultural_theme} wedding orchestration designed to host {guest_count} guests with regal hospitality and disciplined capital allocation.",
            "venue_decor": base["venue_decor"],
            "catering_hospitality": base["catering_hospitality"],
            "photography_makeup": base["photography_makeup"],
            "wedding_financial_rules": [
                "Book venue for Friday evening or Sunday morning to achieve 35% discount over Saturday prime rates.",
                "Commission bespoke live artisanal food counters rather than 6-course plated menus to reduce kitchen labor fees.",
                "Purchase floral focal points in reusable modular stands that transition seamlessly from ceremony to reception."
            ]
        }


def generate_grocery_plan(
    household_size: int,
    dietary_regime: str,
    weekly_budget: float,
    currency: str = "$",
    custom_notes: str = "",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Generates high-nutrition, low-waste grocery and meal prep plans."""
    try:
        from services.gemini_service import get_gemini_client
        client = get_gemini_client(api_key=api_key)
        
        prompt = f"""
You are PocketSmart AI's Clinical Nutrition Economist.
Generate an optimal weekly grocery basket and meal blueprint.

Parameters:
- Household Size: {household_size} Persons
- Dietary Paradigm: {dietary_regime} (e.g. High Protein Mediterranean, Clean Keto, Plant-Based Whole Foods)
- Weekly Budget: {currency}{weekly_budget:,.2f}
- Preferences: {custom_notes}

Respond strictly in JSON matching:
{{
  "household_size": {household_size},
  "dietary_regime": "{dietary_regime}",
  "weekly_budget": {weekly_budget},
  "allocated_budget": 0.0,
  "cost_per_meal": 0.0,
  "currency": "{currency}",
  "nutrition_summary": "Macronutrient balance and gut health focus",
  "grocery_items": [
    {{"item": "Basket Category & Items", "cost": 40.0, "store": "Recommended Market / Store", "tip": "Smart buying tip"}}
  ],
  "batch_prep_protocol": ["Step 1", "Step 2", "Step 3"]
}}
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        base_items = FALLBACK_GROCERY_PLANS["Balanced Nutrition Blueprint"]
        total_base = sum(it["cost"] for it in base_items)
        scale = (weekly_budget * 0.92) / max(total_base, 1.0)
        
        scaled = []
        for it in base_items:
            c = dict(it)
            c["cost"] = round(it["cost"] * scale, 2)
            c["currency"] = currency
            scaled.append(c)
            
        allocated = sum(c["cost"] for c in scaled)
        meals_count = household_size * 21
        return {
            "household_size": household_size,
            "dietary_regime": dietary_regime,
            "weekly_budget": weekly_budget,
            "allocated_budget": round(allocated, 2),
            "cost_per_meal": round(weekly_budget / max(meals_count, 1), 2),
            "currency": currency,
            "nutrition_summary": f"A clean, micronutrient-dense {dietary_regime} whole food portfolio tailored for {household_size} individuals, optimizing protein bioavailability and zero produce waste.",
            "grocery_items": scaled,
            "batch_prep_protocol": [
                "Roast 3 sheet pans of root vegetables and complex carbohydrates on Sunday evening.",
                "Sous-vide or slow-cook proteins in batch marinades for rapid 5-minute weekday assembly.",
                "Store washed greens with reusable paper towels in airtight glass containers to extend crisp freshness to 12 days."
            ]
        }


def generate_student_plan(
    academic_level: str,
    monthly_allowance: float,
    currency: str = "$",
    city_tier: str = "Metropolitan Hub",
    custom_notes: str = "",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Generates undergraduate / graduate monthly student survival and lifestyle budget allocation."""
    try:
        from services.gemini_service import get_gemini_client
        client = get_gemini_client(api_key=api_key)
        
        prompt = f"""
You are PocketSmart AI's Collegiate Financial Counselor.
Create a zero-debt monthly living budget for a student.

Parameters:
- Academic Level: {academic_level} (Undergrad / Master's / PhD)
- Monthly Budget: {currency}{monthly_allowance:,.2f}
- City Tier: {city_tier}
- Notes: {custom_notes}

Respond strictly in JSON matching:
{{
  "academic_level": "{academic_level}",
  "monthly_allowance": {monthly_allowance},
  "allocated_budget": 0.0,
  "daily_discretionary": 0.0,
  "currency": "{currency}",
  "strategy_summary": "Financial survival and social wellness balance",
  "allocation_categories": [
    {{"category": "Expense Line Item", "estimated_cost": 150.0, "hack": "Student discount or bypass tip"}}
  ],
  "student_survival_commandments": ["Tip 1", "Tip 2", "Tip 3"]
}}
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        base = FALLBACK_STUDENT_PLANS["Semester Survival Allocation"]
        daily = round((monthly_allowance * 0.25) / 30, 2)
        return {
            "academic_level": academic_level,
            "monthly_allowance": monthly_allowance,
            "allocated_budget": round(monthly_allowance * 0.92, 2),
            "daily_discretionary": daily,
            "currency": currency,
            "strategy_summary": f"Disciplined cash-flow matrix for {academic_level} scholars in {city_tier}, eliminating overdraft debt while maintaining high academic output and social vitality.",
            "allocation_categories": base,
            "student_survival_commandments": [
                "Utilize student ID for 50% discount on GitHub Copilot, Spotify, Apple Music, and Adobe Creative Cloud.",
                "Cook communal dinners with roommates 4 nights a week to slash per-portion meal expenses by 65%.",
                "Buy certified refurbished laptops with manufacturer warranties rather than expensive retail financing."
            ]
        }

