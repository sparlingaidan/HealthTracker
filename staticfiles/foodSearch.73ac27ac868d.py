import requests
import logging
from catalog.models import FoodItem

logger = logging.getLogger(__name__)


def get_nutrient_amounts(nutrientsList):
    amounts = {"Total lipid (fat)": 0,
               'Fatty acids, total saturated': 0,
               'Fatty acids, total trans': 0,
               'Cholesterol': 0,
               'Sodium, Na': 0,
               'Carbohydrate, by difference': 0,
               'Fiber, total dietary': 0,
               'Total Sugars': 0,
               'Protein': 0,  # 1003
               'Calcium, Ca': 0,
               'Iron, Fe': 0,
               'Potassium, K': 0,
               'Magnesium, Mg': 0,
               'Phosphorus, P': 0,
               'Zinc, Zn': 0,
               'Energy': 0,
               'Vitamin C, total ascorbic acid': 0,
               'Vitamin D (D2 + D3), International Units': 0}
    for i in range(len(nutrientsList)):
        currentNutrient = nutrientsList[i]
        if (currentNutrient['nutrientName'] in amounts):
            amounts[currentNutrient['nutrientName']] = currentNutrient["value"]
    return amounts


def get_food_data(query):
    try:
        key = 'glb9XFdhGGdEZ1pnLb7Xoi06Xc2BvCuhK17UQwWr'
        url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={key}&query={query}"
        response = requests.get(url)
        response.raise_for_status()
        resp = response.json()
        returnedFoods = resp["foods"]
        maxListLength = 30
        foodList = []
        for i in range(len(returnedFoods)):
            inFoodItem = returnedFoods[i]
            brandName = inFoodItem["foodCategory"]
            if "brandName" in inFoodItem:
                brandName = inFoodItem['brandName']
            inFoodName = brandName + ": " + inFoodItem['description']
            inFoodfdcId = inFoodItem['fdcId']
            nutrientDict = get_nutrient_amounts(inFoodItem['foodNutrients'])

            foodItemInstance = FoodItem(
                foodName=inFoodName,
                fdcId=inFoodfdcId,
                fat=nutrientDict["Total lipid (fat)"],
                saturatedFat=nutrientDict["Fatty acids, total saturated"],
                transFat=nutrientDict["Fatty acids, total trans"],
                cholesterol=nutrientDict["Cholesterol"],
                sodium=nutrientDict["Sodium, Na"],
                carbohydrates=nutrientDict["Carbohydrate, by difference"],
                fiber=nutrientDict["Fiber, total dietary"],
                sugars=nutrientDict["Total Sugars"],
                protein=nutrientDict["Protein"],
                calcium=nutrientDict["Calcium, Ca"],
                iron=nutrientDict["Iron, Fe"],
                potassium=nutrientDict["Potassium, K"],
                magnesium=nutrientDict["Magnesium, Mg"],
                phosphorus=nutrientDict["Phosphorus, P"],
                zinc=nutrientDict["Zinc, Zn"],
                calories=nutrientDict["Energy"],
                vitaminC=nutrientDict["Vitamin C, total ascorbic acid"],
                vitaminD=nutrientDict["Vitamin D (D2 + D3), International Units"],
            )
            if not FoodItem.objects.filter(fdcId=inFoodfdcId).exists():
                foodItemInstance.save()
            foodList.append(foodItemInstance)
            maxListLength -= 1
            if (maxListLength < 1):
                break
        return foodList
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to retrieve food data: {e}")
        return None

def get_food_by_fdcId(fdcId):
    return FoodItem.objects.get(fdcId = fdcId)