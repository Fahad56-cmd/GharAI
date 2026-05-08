from price_loader import load_prices

def calculate_areas(length, width, height):
    floor_area   = length * width
    wall_area    = 2 * (length * height) + 2 * (width * height)
    ceiling_area = length * width
    return {"floor_area": floor_area, "wall_area": wall_area, "ceiling_area": ceiling_area}

def calculate_material_quantities(floor_area, wall_area, ceiling_area, floor_material, wall_finish):
    p = load_prices()
    waste = p["flooring"][floor_material]["waste_factor"]
    quantities = {"floor_sqft": round(floor_area * waste, 1)}

    if wall_finish == "paint":
        liters = (wall_area / p["walls"]["paint"]["coverage_sqft_per_liter"]) * p["walls"]["paint"]["coats"]
        quantities["wall_paint_liters"] = round(liters, 1)
    else:
        kgs = wall_area / p["walls"]["texture"]["coverage_sqft_per_kg"]
        quantities["wall_texture_kg"] = round(kgs, 1)

    ceil_liters = (ceiling_area / p["ceiling"]["coverage_sqft_per_liter"]) * p["ceiling"]["coats"]
    quantities["ceiling_paint_liters"] = round(ceil_liters, 1)
    return quantities

def calculate_costs(quantities, floor_material, wall_finish):
    p = load_prices()
    fp = p["flooring"][floor_material]
    floor_cost  = quantities["floor_sqft"] * fp["price_per_sqft"]
    floor_labor = quantities["floor_sqft"] * fp["labor_per_sqft"]

    if wall_finish == "paint":
        wall_cost  = quantities["wall_paint_liters"] * p["walls"]["paint"]["price_per_liter"]
        wall_labor = quantities.get("wall_sqft", quantities["floor_sqft"]) * p["walls"]["paint"]["labor_per_sqft"]
    else:
        wall_cost  = quantities["wall_texture_kg"] * p["walls"]["texture"]["price_per_kg"]
        wall_labor = quantities.get("wall_sqft", quantities["floor_sqft"]) * p["walls"]["texture"]["labor_per_sqft"]

    ceil_cost  = quantities["ceiling_paint_liters"] * p["ceiling"]["price_per_liter"]
    ceil_labor = quantities["ceiling_paint_liters"] * 12 * p["ceiling"]["labor_per_sqft"]

    subtotal    = floor_cost + floor_labor + wall_cost + wall_labor + ceil_cost + ceil_labor
    contingency = subtotal * (p["contingency_percent"] / 100)

    return {
        "Floor material":  round(floor_cost),
        "Floor labor":     round(floor_labor),
        "Wall material":   round(wall_cost),
        "Wall labor":      round(wall_labor),
        "Ceiling material":round(ceil_cost),
        "Ceiling labor":   round(ceil_labor),
        "Contingency":     round(contingency),
    }

def get_total_cost(cost_breakdown):
    return sum(cost_breakdown.values())