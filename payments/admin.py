from django.contrib import admin
from django.utils.html import format_html
from .models import Payment, UserProfile


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment model"""
    
    list_display = [
        'reference', 'user', 'amount_in_naira', 'currency', 
        'status_badge', 'webhook_verified', 'created_at'
    ]
    
    list_filter = [
        'status', 'currency', 'webhook_received', 'webhook_verified', 
        'created_at', 'paid_at'
    ]
    
    search_fields = [
        'reference', 'customer_email', 'user__email', 
        'user__username', 'access_code'
    ]
    
    readonly_fields = [
        'id', 'reference', 'created_at', 'updated_at', 
        'paid_at', 'paystack_response', 'webhook_received'
    ]
    
    fieldsets = [
        ('Payment Information', {
            'fields': (
                'reference', 'user', 'customer_email', 'amount', 
                'currency', 'status'
            )
        }),
        ('Paystack Integration', {
            'fields': (
                'authorization_url', 'access_code', 'paystack_response'
            ),
            'classes': ('collapse',)
        }),
        ('Webhook Status', {
            'fields': (
                'webhook_received', 'webhook_verified'
            )
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at'),
            'classes': ('collapse',)
        })
    ]
    
    def status_badge(self, obj):
        """Display colored status badge"""
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'success': 'green',
            'failed': 'red',
            'cancelled': 'gray',
            'abandoned': 'darkred'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def amount_in_naira(self, obj):
        """Display amount in Naira"""
        return f"₦{obj.amount_in_naira:,.2f}"
    amount_in_naira.short_description = 'Amount (₦)'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model"""
    
    list_display = ['user', 'payment_status_badge', 'created_at']
    list_filter = ['payment_status', 'created_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    def payment_status_badge(self, obj):
        """Display colored payment status badge"""
        colors = {
            'pending': 'orange',
            'completed': 'green',
            'failed': 'red',
            'refunded': 'blue'
        }
        color = colors.get(obj.payment_status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'Payment Status'
