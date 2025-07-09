from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MnoryUser, VendorProfile


@receiver(post_save, sender=MnoryUser)
def create_vendor_profile(sender, instance, created, **kwargs):
    if created and instance.is_vendor:
        # This is where the problematic creation happens
        VendorProfile.objects.create(user=instance)