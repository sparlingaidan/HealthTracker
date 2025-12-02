from django.db import models
from django.contrib.auth.models import User


# Create your models here.
# Django User already provides username, password, etc
# https://docs.djangoproject.com/en/5.2/ref/contrib/auth/
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    birthdate = models.DateField(null=True, blank=True)
    age = models.PositiveIntegerField(null=False)
    height = models.FloatField(null=False)
    weight = models.FloatField(null=False)
    gender = models.BooleanField(null=True)

    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)

    def __str__(self):
        return self.user.username


class FoodItem(models.Model):
    # brandName + ": " + description
    foodName = models.CharField(null=False, max_length=255)
    fdcId = models.PositiveIntegerField(null=True, unique=True)
    fat = models.FloatField(default=0)  
    saturatedFat = models.FloatField(default=0)
    transFat = models.FloatField(default=0)
    cholesterol = models.FloatField(default=0)
    sodium = models.FloatField(default=0)
    carbohydrates = models.FloatField(default=0)
    fiber = models.FloatField(default=0)
    sugars = models.FloatField(default=0)
    protein = models.FloatField(default=0) # 1003
    calcium = models.FloatField(default=0)
    iron = models.FloatField(default=0)
    potassium = models.FloatField(default=0)
    magnesium = models.FloatField(default=0)
    phosphorus = models.FloatField(default=0)
    zinc = models.FloatField(default=0)
    calories = models.FloatField(default=0)
    vitaminC = models.FloatField(default=0)
    vitaminD = models.FloatField(default=0)

    def __str__(self):
        return self.foodName


class LogItem(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now=False, auto_now_add=False)
    foodItem = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    # I assume use a float from 0 to 1
    percentConsumed = models.FloatField(default=1)

    def __str__(self):
        return (self.profile.user.username + ":" + self.foodItem.foodName + ":" + self.date.strftime("%B"))
