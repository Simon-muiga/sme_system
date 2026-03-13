from django.contrib import admin
from .models import BusinessProfile, Category, Sale, Expense, Prediction

admin.site.register(BusinessProfile)
admin.site.register(Category)
admin.site.register(Sale)
admin.site.register(Expense)
admin.site.register(Prediction)

