# vendors/ai_combo.py
import random
from decimal import Decimal
from menuitem.models import MenuItem

HEALTH_TIPS = [
    lambda c, p, carbs, fat: "Perfect light breakfast with steady energy." if c < 400 else "",
    lambda c, p, carbs, fat: "Rich in protein — good for muscle recovery." if p > 10 else "",
    lambda c, p, carbs, fat: "High in carbs — keeps you energetic for long hours." if carbs > 40 else "",
    lambda c, p, carbs, fat: "Low fat & easy to digest." if fat < 5 else "",
    lambda c, p, carbs, fat: "Balanced meal with protein, carbs & fiber." if 300 < c < 600 else "",
]

def generate_ai_combos(vendor, max_combos: int = 5):
    """
    AI-inspired combo builder with nutrition & health tips.
    """
    items = MenuItem.objects.filter(vendor=vendor, is_available=True)
    if not items.exists():
        return []

    categories = {}
    for item in items:
        categories.setdefault(str(item.category), []).append(item)

    combos = []
    for _ in range(max_combos):
        combo_items = []
        subtotal = Decimal("0.00")
        total_cal, total_protein, total_carbs, total_fat = 0, 0, 0, 0

        # pick at least 1 from each category
        for _, cat_items in categories.items():
            chosen = random.choice(cat_items)
            combo_items.append(chosen)
            subtotal += chosen.price
            total_cal += float(chosen.calories)
            total_protein += float(chosen.protein)
            total_carbs += float(chosen.carbs)
            total_fat += float(chosen.fat)

        # discount
        discount = Decimal("0.00")
        if subtotal > 200:
            discount = subtotal * Decimal("0.10")

        total_price = subtotal - discount

        # generate health tip
        tips = []
        for rule in HEALTH_TIPS:
            msg = rule(total_cal, total_protein, total_carbs, total_fat)
            if msg:
                tips.append(msg)
        health_tip = " ".join(tips) if tips else "Nutritious & filling combo."

        combos.append({
            "items": [i.name for i in combo_items],
            "subtotal": float(subtotal),
            "discount": float(discount),
            "final_price": float(total_price),
            "nutrition": {
                "calories": total_cal,
                "protein": total_protein,
                "carbs": total_carbs,
                "fat": total_fat,
            },
            "health_tip": health_tip,
        })

    return combos
