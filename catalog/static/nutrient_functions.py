from catalog.models import FoodItem, LogItem, Profile

nutrient_fields = [
    "fat",
    "saturatedFat",
    "transFat",
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
    "calories",
    "vitaminC",
    "vitaminD",
]


# https://www.fda.gov/media/99069/download
nutrient_ranges = {
    "fat": {"min": 50, "max": 70, "target": 78},  # g, ~25–35% of calories
    "saturatedFat": {"min": 0, "max": 20, "target": 20},  # g, aim <10% of calories
    "transFat": {"min": 0, "max": 2, "target": 0},  # g, keep as low as possible
    "cholesterol": {"min": 125, "max": 300, "target": 300},  # mg
    "sodium": {"min": 1500, "max": 2300, "target": 2300},  # mg
    "carbohydrates": {"min": 225, "max": 325, "target": 275},  # g, 45–65% calories
    "fiber": {"min": 25, "max": 35, "target": 28},  # g
    "sugars": {"min": 0, "max": 50, "target": 50},  # g, added sugars DV
    "protein": {"min": 45, "max": 65, "target": 50},  # g
    "calcium": {"min": 700, "max": 1200, "target": 1000},  # mg
    "iron": {"min": 8, "max": 18, "target": 18},  # mg
    "potassium": {"min": 2600, "max": 4700, "target": 4700},  # mg
    "magnesium": {"min": 310, "max": 420, "target": 420},  # mg (adult male)
    "phosphorus": {"min": 700, "max": 1250, "target": 1250},  # mg
    "zinc": {"min": 8, "max": 11, "target": 11},  # mg
    "calories": {"min": 1800, "max": 2500, "target": 2000},  # kcal
    "vitaminC": {"min": 75, "max": 200, "target": 90},  # mg
    "vitaminD": {"min": 15, "max": 20, "target": 20},  # µg (600–800 IU)
}


def Deviation(field, value):
    """
    Calculate the normalized deviation of a nutrient value from its target.

    Parameters
    field : str
        The key identifying which nutrient's range and target to use from
        `nutrient_ranges`.
    value : float or int
        The actual measured value of the nutrient.

    Returns
    float
        A normalized deviation value where:
        - 0 indicates the value is exactly at the target,
        - 1 indicates the value is one "half-range" away from the target,
        - Values > 1 indicate larger deviations.

    """
    deviation_size = (nutrient_ranges[field]["max"] - nutrient_ranges[field]["min"]) / 2
    target = nutrient_ranges[field]["target"]
    deviation = abs(target - value) / deviation_size
    return deviation


def get_dv_avg(start, end, profileId):
    """
    For generating an average of the nutrients consumed.

    This function is for returning the date to be used in
    _nutrient_gauge.html.  It averages all nutrients consumed
    from start to end.

    Args:
        start (DateTimeField): Begining of the period to be averaged.
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
            'deviation': deviation,
            }
        }
    """

    searchProfile = Profile.objects.get(id=profileId)
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

    results = {}
    for field in nutrient_fields:
        avg_value = getattr(tempFoodItem, field, 0)
        deviation = Deviation(field, avg_value)

        results[field] = {
            "minIn": nutrient_ranges[field]["min"],
            "maxIn": nutrient_ranges[field]["max"],
            "maxRange": int(nutrient_ranges[field]["max"] * 1.2),
            "value": avg_value,
            "deviation": deviation
        }
    return results


def get_log_items(start, end, profileId):
    searchProfile = Profile.objects.get(id=profileId)
    results = LogItem.objects.filter(
        profile=searchProfile, date__gte=start, date__lte=end
    )
    return results.order_by("-date")
