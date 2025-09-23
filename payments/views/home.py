"""
Homepage views for testing the payment system.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView
from ..models import Payment


class HomePageView(TemplateView):
    """Homepage view with payment testing interface."""
    
    template_name = 'payments/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get recent payments for display
        context['recent_payments'] = Payment.objects.select_related('user').order_by('-created_at')[:10]
        context['total_payments'] = Payment.objects.count()
        context['successful_payments'] = Payment.objects.filter(status='success').count()
        context['pending_payments'] = Payment.objects.filter(status='pending').count()
        
        return context


def payment_stats_api(request):
    """API endpoint for payment statistics."""
    stats = {
        'total_payments': Payment.objects.count(),
        'successful_payments': Payment.objects.filter(status='success').count(),
        'pending_payments': Payment.objects.filter(status='pending').count(),
        'failed_payments': Payment.objects.filter(status='failed').count(),
        'recent_payments': []
    }
    
    # Get recent payments
    recent_payments = Payment.objects.select_related('user').order_by('-created_at')[:5]
    for payment in recent_payments:
        stats['recent_payments'].append({
            'reference': payment.reference,
            'amount': float(payment.amount_in_naira),
            'status': payment.status,
            'customer_email': payment.customer_email,
            'created_at': payment.created_at.isoformat()
        })
    
    return JsonResponse(stats)