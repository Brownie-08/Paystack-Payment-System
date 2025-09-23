import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone


class UserProfile(models.Model):
    """Extended User profile with payment status tracking"""
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        help_text="Current payment status for the user"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} ({self.get_payment_status_display()})"
    
    class Meta:
        db_table = 'payments_user_profile'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


# Signal handlers are now in signals.py


class Payment(models.Model):
    """Payment model for tracking Paystack transactions"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('abandoned', 'Abandoned'),
    ]
    
    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique payment reference for idempotency"
    )
    
    # Relationship to user
    user = models.ForeignKey(
        'auth.User',  # Use the default User model for now
        on_delete=models.CASCADE,
        related_name='payments',
        help_text="User who initiated the payment"
    )
    
    # Payment details
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('1.00'))],
        help_text="Amount in kobo (Nigerian currency subunit)"
    )
    
    currency = models.CharField(
        max_length=3,
        default='NGN',
        help_text="Payment currency code"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Current payment status"
    )
    
    # Paystack integration data
    paystack_response = models.JSONField(
        default=dict,
        blank=True,
        help_text="Raw response data from Paystack API"
    )
    
    authorization_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Paystack checkout URL for the payment"
    )
    
    access_code = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Paystack access code for the transaction"
    )
    
    # Webhook data
    webhook_received = models.BooleanField(
        default=False,
        help_text="Whether webhook notification was received"
    )
    
    webhook_verified = models.BooleanField(
        default=False,
        help_text="Whether payment was verified via Paystack API"
    )
    
    # Customer information
    customer_email = models.EmailField(
        help_text="Customer email address for the payment"
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional payment metadata"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the payment record was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the payment record was last updated"
    )
    
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the payment was completed"
    )
    
    # Amount helpers
    @property
    def amount_in_naira(self):
        """Convert kobo amount to Naira for display purposes"""
        return self.amount / 100
    
    @classmethod
    def naira_to_kobo(cls, naira_amount):
        """Convert Naira amount to kobo for API calls"""
        return Decimal(str(naira_amount)) * 100
    
    def mark_as_paid(self):
        """Mark payment as successful and update timestamps"""
        self.status = 'success'
        self.paid_at = timezone.now()
        self.webhook_verified = True
        self.save(update_fields=['status', 'paid_at', 'webhook_verified', 'updated_at'])
    
    def mark_as_failed(self, reason=None):
        """Mark payment as failed"""
        self.status = 'failed'
        if reason:
            if 'metadata' not in self.metadata:
                self.metadata['failure_reason'] = reason
        self.save(update_fields=['status', 'metadata', 'updated_at'])
    
    def __str__(self):
        return f"Payment {self.reference} - {self.get_status_display()} - ₦{self.amount_in_naira:.1f}"
    
    class Meta:
        db_table = 'payments_payment'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['customer_email']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['reference'],
                name='unique_payment_reference'
            ),
        ]
