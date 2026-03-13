from django.urls import path
from . import views
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-expense/', views.add_expense, name='add_expense'),
    path('add-sale/', views.add_sale, name='add_sale'),  # ✅ fixed
    path('edit-sale/<int:pk>/', views.edit_sale, name='edit_sale'),
    path('delete-sale/<int:pk>/', views.delete_sale, name='delete_sale'),
    path('edit-expense/<int:pk>/', views.edit_expense, name='edit_expense'),
    path('delete-expense/<int:pk>/', views.delete_expense, name='delete_expense'),
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='finance/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('create-business-profile/', views.create_business_profile, name='create_business_profile'),
    path('download-report/', views.download_report, name='download_report')
    


]
