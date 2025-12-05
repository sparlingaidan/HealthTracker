from catalog.models import FoodItem, LogItem, Profile

nutrient_fields = [
    "fat",
    "saturatedFat",
    "transFat",
    "calories",
    "cholesterol",
    "sodium",
    "carbohydrates",
    "fiber",
    "sugars",
    "protein",
    "calcium",
    "iron",
    "potassium",
    "magnesium",
    "phosphorus",
    "zinc",
    "vitaminC",
    "vitaminD",
]


# https://www.fda.gov/media/99069/download
nutrient_ranges = {
    "fat": {"min": 50, "max": 70, "target": 78},  # g, 30% of calories
    "saturatedFat": {"min": 0, "max": 20, "target": 20},  # g, aim <10% of calories
    "transFat": {"min": 0, "max": 20, "target": 0},  # g, keep as low as possible
    "cholesterol": {"min": 50, "max": 200, "target": 10},  # 0 mg
    "sodium": {"min": 1500, "max": 2300, "target": 2300},  #2300 mg
    "carbohydrates": {"min": 225, "max": 325, "target": 275},  # g, 130 + 50% calories
    "fiber": {"min": 25, "max": 35, "target": 28},  # g, calories * 0.0714
    "sugars": {"min": 0, "max": 50, "target": 50},  # g, aim <10% of calories
    "protein": {"min": 45, "max": 65, "target": 50},  # g, 2.2 g per kg
    "calcium": {"min": 700, "max": 1200, "target": 1000},  # 1000 mg
    "iron": {"min": 8, "max": 85, "target": 8},  # 8 mg
    "potassium": {"min": 2600, "max": 4700, "target": 4700},  # 3400 mg
    "magnesium": {"min": 320, "max": 400, "target": 400},  # mg 400-420
    "phosphorus": {"min": 700, "max": 3000, "target": 700},  # mg 700
    "zinc": {"min": 11, "max": 40, "target": 11},  # mg 11
    "calories": {"min": 1800, "max": 2500, "target": 2000},  # kcal 864 - 9.72 * Age (years) + 1.27 * (14.2 * Weight (kg) + 503 * Height (meters) )
    "vitaminC": {"min": 90, "max": 2000, "target": 90},  # mg 90
    "vitaminD": {"min": 600, "max": 4000, "target": 600},  # µg (600–800 IU)
}


spread = 0.15
def make_min(value):
    return (value - (value * spread))

def make_max(value):
    return (value + (value * spread))

def personalize(ranges, profile):
    age = profile.age
    height = profile.height / 100
    weight = profile.weight
    if profile.gender == 'F':
        # Calorie
        calTarget = 387 - 7.31 * age + 1.27 * (10.9 * weight + 660.7 * height )
        ranges['calories']['target'] = calTarget
        ranges['calories']['min'] = make_min(calTarget)
        ranges['calories']['max'] = make_max(calTarget)
        ranges['iron'] = {"min": 18, "max": 95, "target": 18}  # 8 mg
        ranges["potassium"] = {"min": 2000, "max": 4000, "target": 2600}
        ranges["vitaminC"] = {"min": 70, "max": 2000, "target": 70}
        ranges["zinc"] = {"min": 8, "max": 35, "target": 8}
        if age > 29:
            ranges['magnesium'] = {"min": 350, "max": 420, "target": 420}
        else:
            ranges['magnesium'] = {"min": 250, "max": 310, "target": 310}
    else:
        # Calorie
        calTarget = 864 - 9.72 * age + 1.27 * (14.2 * weight + 503 * height )
        ranges['calories']['target'] = calTarget
        ranges['calories']['min'] = make_min(calTarget)
        ranges['calories']['max'] = make_max(calTarget)
        if age > 29:
            ranges['magnesium'] = {"min": 350, "max": 420, "target": 420}

    # Fat = 30% calories. 1 fat == 9 kcal
    fatTarget = (calTarget / 9) * 0.30
    ranges['fat']['target'] = fatTarget
    ranges['fat']['min'] = make_min(fatTarget)
    ranges['fat']['max'] = make_max(fatTarget)
    # satFat = 30% calories. 1 fat == 9 kcal
    satFatTarget = (calTarget / 9) * 0.10
    ranges['saturatedFat']['target'] = satFatTarget
    ranges['saturatedFat']['min'] = make_min(satFatTarget)
    ranges['saturatedFat']['max'] = make_max(satFatTarget)
    # Carb = 130 + 50% calories. 1 carb == 4 kcal
    carTarget = 130 + ( (calTarget / 4) * 0.50 )
    ranges['carbohydrates']['target'] = carTarget
    ranges['carbohydrates']['min'] = make_min(carTarget)
    ranges['carbohydrates']['max'] = make_max(carTarget)
    # Fiber = calories * 0.0714
    fiberTarget = 130 + ( (calTarget / 4) * 0.50 )
    ranges['fiber']['target'] = fiberTarget
    ranges['fiber']['min'] = make_min(fiberTarget)
    ranges['fiber']['max'] = make_max(fiberTarget)
    # Sugars = 10% calories. 1 sugar == 4 kcal
    sugarTarget = (calTarget / 9) * 0.10
    ranges['sugars']['target'] = sugarTarget
    ranges['sugars']['min'] = make_min(sugarTarget)
    ranges['sugars']['max'] = make_max(sugarTarget)
    # Protein = 2.2 per kg
    proTarget = weight * 2.2
    ranges['protein']['target'] = proTarget
    ranges['protein']['min'] = make_min(proTarget)
    ranges['protein']['max'] = make_max(proTarget)
    return ranges

def get_dv_avg(start, end, profileId):
    """
    For generating an average of the nutrients consumed.

    This function is for returning the date to be used in
    _nutrient_gauge.html.  It averages all nutrients consumed
    from start to end.

    Args:
        start (DateTimeField): Beginning of the period to be averaged.
        end (DateTimeField): End of the period to be averaged.
        profileId (int): Id number of the profile to average.

    Returns:
        Dictionary:
        {
        'name': name
            {
            'minIn': minIn,
            'maxIn': maxIn,
            'maxRange': maxRange,
            'value': value,
            }
        }
    """

    searchProfile = Profile.objects.get(id=profileId)
    gender = searchProfile.gender
    logQuery = LogItem.objects.filter(
        profile=searchProfile, date__gte=start, date__lte=end
    )
    tempFoodItem = FoodItem()

    logLen = (end - start).total_seconds() / 86400

    for field in nutrient_fields:  # For Each nutrient
        values = [  # Go through all of the returned log items.
            (getattr(item.foodItem, field, 0) or 0) * (item.percentConsumed or 0)
            for item in logQuery
        ]
        total = sum(values)
        avg = total / logLen if logLen else 0 # Average the value
        setattr(tempFoodItem, field, avg)

    personal_ranges = personalize(nutrient_ranges, searchProfile)

    results = {}
    for field in nutrient_fields:
        avg_value = getattr(tempFoodItem, field, 0)

        results[field] = {
            "minIn": personal_ranges[field]["min"],
            "maxIn": personal_ranges[field]["max"],
            "maxRange": int(personal_ranges[field]["max"] * 1.2),
            "value": avg_value,
        }
    return results


def get_log_items(start, end, profileId):
    searchProfile = Profile.objects.get(id=profileId)
    results = LogItem.objects.filter(
        profile=searchProfile, date__gte=start, date__lte=end
    )
    return results.order_by("-date")
