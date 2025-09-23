"""
Django REST Framework serializers for the payments app.
"""

from decimal import Decimal, InvalidOperation
from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Payment, UserProfile


class PaymentInitializeSerializer(serializers.Serializer):
    """Serializer for payment initialization requests"""
    
    email = serializers.EmailField(
        help_text="Customer's email address"
    )
    
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('1.00'),
        help_text="Amount in Naira (minimum ₦1.00)"
    )
    
    callback_url = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text="Optional callback URL for payment completion redirect"
    )
    
    def validate_amount(self, value):
        """Validate amount is reasonable"""
        if value > Decimal('1000000.00'):  # 1M Naira limit
            raise serializers.ValidationError(
                "Amount cannot exceed ₦1,000,000.00"
            )
        return value


class PaymentInitializeResponseSerializer(serializers.Serializer):
    """Serializer for payment initialization responses"""
    
    reference = serializers.CharField(
        help_text="Unique payment reference"
    )
    
    authorization_url = serializers.URLField(
        help_text="Paystack checkout URL"
    )
    
    access_code = serializers.CharField(
        help_text="Paystack access code"
    )
    
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Payment amount in Naira"
    )
    
    customer_email = serializers.EmailField(
        help_text="Customer's email address"
    )
    
    status = serializers.CharField(
        help_text="Payment status"
    )
    
    created_at = serializers.DateTimeField(
        help_text="Payment creation timestamp"
    )


class PaymentListSerializer(serializers.ModelSerializer):
    """Serializer for payment list/detail views"""
    
    amount_in_naira = serializers.ReadOnlyField(
        help_text="Amount in Naira for display"
    )
    
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True,
        help_text="Human-readable status"
    )
    
    class Meta:
        model = Payment
        fields = [
            'id', 'reference', 'customer_email', 'amount', 
            'amount_in_naira', 'currency', 'status', 'status_display',
            'authorization_url', 'webhook_received', 'webhook_verified',
            'created_at', 'updated_at', 'paid_at'
        ]
        read_only_fields = [
            'id', 'reference', 'amount', 'currency', 'status',
            'authorization_url', 'webhook_received', 'webhook_verified',
            'created_at', 'updated_at', 'paid_at'
        ]


class PaymentDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed payment views"""
    
    amount_in_naira = serializers.ReadOnlyField()
    status_display = serializers.CharField(
        source='get_status_display', 
        read_only=True
    )
    
    user_email = serializers.CharField(
        source='user.email',
        read_only=True
    )
    
    class Meta:
        model = Payment
        fields = [
            'id', 'reference', 'user_email', 'customer_email', 
            'amount', 'amount_in_naira', 'currency', 'status', 
            'status_display', 'authorization_url', 'access_code',
            'webhook_received', 'webhook_verified', 'metadata',
            'created_at', 'updated_at', 'paid_at'
        ]
        read_only_fields = [
            'id', 'reference', 'user_email', 'customer_email', 
            'amount', 'amount_in_naira', 'currency', 'status', 
            'status_display', 'authorization_url', 'access_code',
            'webhook_received', 'webhook_verified', 'metadata',
            'created_at', 'updated_at', 'paid_at'
        ]


class PaymentVerificationResponseSerializer(serializers.Serializer):
    """Serializer for payment verification responses"""
    
    reference = serializers.CharField()
    status = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    customer_email = serializers.EmailField()
    paid_at = serializers.DateTimeField(allow_null=True)
    verification_data = serializers.DictField(
        help_text="Raw Paystack verification response"
    )


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile with payment status"""
    
    user_email = serializers.CharField(
        source='user.email',
        read_only=True
    )
    
    payment_status_display = serializers.CharField(
        source='get_payment_status_display',
        read_only=True
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'user_email', 'payment_status', 'payment_status_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class WebhookEventSerializer(serializers.Serializer):
    """Serializer for webhook event data"""
    
    event = serializers.CharField(
        help_text="Webhook event type"
    )
    
    data = serializers.DictField(
        help_text="Webhook event data"
    )
    
    def validate_event(self, value):
        """Validate supported webhook events"""
        supported_events = ['charge.success', 'charge.failed']
        if value not in supported_events:
            raise serializers.ValidationError(
                f"Unsupported event type: {value}. "
                f"Supported events: {', '.join(supported_events)}"
            )
        return value
    
    def validate_data(self, value):
        """Validate webhook data contains required fields"""
        required_fields = ['reference', 'status', 'amount']
        
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(
                    f"Missing required field in data: {field}"
                )
        
        return value


class PaymentCallbackSerializer(serializers.Serializer):
    """Serializer for payment callback parameters"""
    
    reference = serializers.CharField(
        help_text="Payment reference from callback"
    )
    
    trxref = serializers.CharField(
        required=False,
        help_text="Transaction reference (optional)"
    )


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses"""
    
    error = serializers.CharField(
        help_text="Error message"
    )
    
    details = serializers.DictField(
        required=False,
        help_text="Additional error details"
    )
    
    timestamp = serializers.DateTimeField(
        help_text="Error timestamp"
    )