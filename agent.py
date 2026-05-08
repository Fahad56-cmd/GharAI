import os, json
from dotenv import load_dotenv
load_dotenv()
from groq import Groq
from calculations import calculate_areas, calculate_material_quantities, calculate_costs, get_total_cost
from price_loader import load_prices, get_meta

client = Groq(api_key=os.environ["GROQ_API_KEY"])

# ── AGENT 1: Extractor ──────────────────────────────────────────────
class ExtractorAgent:
    def run(self, brief: str) -> dict:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content":
                 "You extract room data from Pakistani interior design briefs. "
                 "Return ONLY a raw JSON object — no markdown, no explanation — with these exact keys: "
                 "length (float, feet), width (float, feet), height (float, default 10.0), "
                 "num_rooms (int, default 1), floor_material (exactly 'marble' or 'porcelain'), "
                 "wall_finish (exactly 'paint' or 'texture'), style (string), budget_pkr (float)."},
                {"role": "user", "content": brief}
            ]
        )
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace("```json","").replace("```","").strip()
        try:
            return json.loads(raw)
        except Exception:
            return {"length":15,"width":12,"height":10,"num_rooms":1,
                    "floor_material":"marble","wall_finish":"texture",
                    "style":"modern","budget_pkr":800000}

# ── AGENT 2: Cost Analyst ───────────────────────────────────────────
class CostAnalystAgent:
    def run(self, room: dict) -> dict:
        areas = calculate_areas(room["length"], room["width"], room["height"])

        # pass wall_area into quantities for labor calc
        quantities = calculate_material_quantities(
            areas["floor_area"], areas["wall_area"], areas["ceiling_area"],
            room["floor_material"], room["wall_finish"]
        )
        quantities["wall_sqft"] = areas["wall_area"]

        costs = calculate_costs(quantities, room["floor_material"], room["wall_finish"])
        total = get_total_cost(costs)

        if room.get("num_rooms", 1) > 1:
            total = round(total * room["num_rooms"] * 0.85)

        return {
            "areas":          areas,
            "quantities":     quantities,
            "cost_breakdown": costs,
            "total_cost":     total,
            "over_budget":    total > room.get("budget_pkr", float("inf")),
            "budget_gap":     total - room.get("budget_pkr", 0),
        }

# ── AGENT 3: Design Advisor ─────────────────────────────────────────
class DesignAdvisorAgent:
    def run(self, room: dict, analysis: dict) -> dict:
        context = (
            f"Style: {room['style']} | Rooms: {room.get('num_rooms',1)} | "
            f"Floor: {room['floor_material']} | Wall: {room['wall_finish']} | "
            f"Budget: PKR {room['budget_pkr']:,.0f} | "
            f"Total cost: PKR {analysis['total_cost']:,.0f} | "
            f"Over budget: {analysis['over_budget']}"
        )
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content":
                 "You are a Pakistani interior design expert with 15 years experience in "
                 "Karachi, Lahore, and Islamabad. Give brutally practical advice. "
                 "Return ONLY a raw JSON object with: "
                 "suggestions (list of exactly 4 strings — each must mention a PKR amount "
                 "or a specific Pakistani city/market), "
                 "style_note (one sentence about this style in Pakistan)."},
                {"role": "user", "content": context}
            ]
        )
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace("```json","").replace("```","").strip()
        try:
            return json.loads(raw)
        except Exception:
            return {
                "suggestions": [
                    "Buy marble in bulk from Karachi's Abdullah Haroon Road to save PKR 40,000+",
                    "For modern style, use light grey tones — hides dust in Pakistani climate",
                    "Add 10% contingency — PKR material prices fluctuate monthly",
                    "Hire labour from local contractors in Model Colony for 20% lower rates"
                ],
                "style_note": "Modern minimalist is the most popular style in Pakistani urban apartments right now."
            }

# ── SUPERVISOR: Runs all 3 agents ──────────────────────────────────
def run_gharai(user_brief: str) -> dict:
    log = []

    extractor = ExtractorAgent()
    room = extractor.run(user_brief)
    log.append(f"✅ ExtractorAgent — {room.get('num_rooms',1)}-room {room.get('style','modern')} project detected")

    analyst = CostAnalystAgent()
    analysis = analyst.run(room)
    log.append(f"✅ CostAnalystAgent — Total PKR {analysis['total_cost']:,.0f} calculated")

    advisor = DesignAdvisorAgent()
    advice = advisor.run(room, analysis)
    log.append(f"✅ DesignAdvisorAgent — {len(advice['suggestions'])} suggestions generated")

    log.append("✅ Supervisor — Report compiled successfully")

    return {
        "room":       room,
        "analysis":   analysis,
        "advice":     advice,
        "agent_log":  log,
        "price_meta": get_meta(),
    }