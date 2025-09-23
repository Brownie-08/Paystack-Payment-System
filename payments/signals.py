"""
Django signals for the payments app.

This module contains signal handlers for payment-related events.
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Payment, UserProfile

logger = logging.getLogger('payments')


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when a new User is created"""
    if created:
        UserProfile.objects.get_or_create(user=instance)
        logger.info(f"Created user profile for {instance.email}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        # Create profile if it doesn't exist
        UserProfile.objects.get_or_create(user=instance)
        logger.info(f"Created missing profile for user {instance.email}")


@receiver(post_save, sender=Payment)
def payment_status_changed(sender, instance, created, **kwargs):
    """Handle payment status changes"""
    if not created and instance.status == 'success':
        # Update user's payment status when payment is successful
        if hasattr(instance.user, 'profile'):
            if instance.user.profile.payment_status != 'completed':
                instance.user.profile.payment_status = 'completed'
                instance.user.profile.save()
                logger.info(f"Updated user payment status to completed: {instance.user.email}")


@receiver(pre_save, sender=Payment)
def log_payment_status_change(sender, instance, **kwargs):
    """Log payment status changes"""
    if instance.pk:  # Only for existing payments
        try:
            old_payment = Payment.objects.get(pk=instance.pk)
            if old_payment.status != instance.status:
                logger.info(
                    f"Payment status changed: {instance.reference} "
                    f"from {old_payment.status} to {instance.status}"
                )
        except Payment.DoesNotExist:
            pass