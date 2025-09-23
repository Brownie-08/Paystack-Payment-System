"""
URL configuration for payments app.
"""

from django.urls import path, include
from .views import (
    PaymentInitializeView,
    PaymentWebhookView,
    PaymentVerifyView,
    PaymentCallbackView,
    PaymentListView,
    PaymentDetailView,
    HomePageView,
    payment_stats_api,
)

app_name = 'payments'

urlpatterns = [
    # Payment initialization
    path('initiate/', PaymentInitializeView.as_view(), name='payment-initiate'),
    
    # Webhook endpoint
    path('webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
    
    # Payment verification
    path('verify/<str:reference>/', PaymentVerifyView.as_view(), name='payment-verify'),
    
    # Payment callback (optional UI flow)
    path('callback/', PaymentCallbackView.as_view(), name='payment-callback'),
    
    # Payment listing and details
    path('', PaymentListView.as_view(), name='payment-list'),
    path('<str:reference>/', PaymentDetailView.as_view(), name='payment-detail'),
]