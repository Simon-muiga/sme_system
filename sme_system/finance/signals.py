# finance/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import BusinessProfile

# When a new user is created, automatically create a BusinessProfile
@receiver(post_save, sender=User)
def create_business_profile(sender, instance, created, **kwargs):
    if created:
        BusinessProfile.objects.create(
            user=instance,
            business_name=f"{instance.username}'s Business",
            industry="General"
        )

# Optional: save the business profile when the user is saved
@receiver(post_save, sender=User)
def save_business_profile(sender, instance, **kwargs):
    try:
        instance.businessprofile.save()
    except BusinessProfile.DoesNotExist:
        pass