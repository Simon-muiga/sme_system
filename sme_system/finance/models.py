from django.db import models
from django.contrib.auth.models import User

# -------------------
# Business Profile
# -------------------
class BusinessProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    business_name = models.CharField(max_length=200)
    industry = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name


# -------------------
# Category
# -------------------
class Category(models.Model):

    CATEGORY_TYPE = (
        ('SALE', 'Sale'),
        ('EXPENSE', 'Expense'),
    )

    business = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=100)

    category_type = models.CharField(
        max_length=10,
        choices=CATEGORY_TYPE
    )

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


# -------------------
# Sale
# -------------------
class Sale(models.Model):
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(auto_now_add=True)  # now editable via form
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Sale - {self.amount}"


# -------------------
# Expense
# -------------------
class Expense(models.Model):
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Expense - {self.amount}"


# -------------------
# Prediction
# -------------------
class Prediction(models.Model):
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE)
    predicted_revenue = models.DecimalField(max_digits=12, decimal_places=2)
    month = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prediction - {self.month}"
