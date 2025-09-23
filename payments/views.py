"""
Django REST Framework views for the payments app.

This module contains all API endpoints for payment processing:
- Payment initialization
- Webhook handling 
- Payment verification
- Payment listing and details
"""

import json
import logging
from decimal import Decimal
from typing import Dict, Any

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import (
    extend_schema, 
    OpenApiParameter, 
    OpenApiResponse,
    OpenApiExample
)

from .models import Payment, UserProfile
from .serializers import (
    PaymentInitializeSerializer,
    PaymentInitializeResponseSerializer,
    PaymentListSerializer,
    PaymentDetailSerializer,
    PaymentVerificationResponseSerializer,
    PaymentCallbackSerializer,
    WebhookEventSerializer,
    ErrorResponseSerializer
)
from .services import PaymentService, PaystackAPIError

logger = logging.getLogger('payments')


class PaymentInitializeView(APIView):
    """
    Initialize a new payment transaction with Paystack.
    
    This endpoint creates a payment record and returns the Paystack checkout URL.
    """
    
    permission_classes = [AllowAny]
    
    @extend_schema(
        operation_id='initialize_payment',
        summary='Initialize Payment',
        description='Initialize a new payment transaction with Paystack',
        request=PaymentInitializeSerializer,
        responses={
            201: OpenApiResponse(
                response=PaymentInitializeResponseSerializer,
                description='Payment initialized successfully'
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Invalid request data'
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Payment initialization failed'
            )
        },
        examples=[
            OpenApiExample(
                'Payment Initialization Request',
                value={
                    'email': 'customer@example.com',
                    'amount': '1000.00',
                    'callback_url': 'https://example.com/payment/callback'
                },
                request_only=True
            ),
            OpenApiExample(
                'Payment Initialization Response',
                value={
                    'reference': 'PAY_20240122123456_ABC12345',
                    'authorization_url': 'https://checkout.paystack.com/xyz123',
                    'access_code': 'xyz123abc',
                    'amount': '1000.00',
                    'customer_email': 'customer@example.com',
                    'status': 'pending',
                    'created_at': '2024-01-22T12:34:56Z'
                },
                response_only=True
            )
        ]
    )
    def post(self, request):
        """Initialize a payment transaction"""
        
        serializer = PaymentInitializeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'Invalid request data',
                    'details': serializer.errors,
                    'timestamp': timezone.now()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        email = validated_data['email']
        amount = validated_data['amount']
        callback_url = validated_data.get('callback_url')
        
        try:
            # Get or create user based on email
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'username': email}
            )
            
            # Create payment using the service
            payment_service = PaymentService()
            payment, paystack_data = payment_service.create_payment(
                user=user,
                customer_email=email,
                amount_naira=amount,
                callback_url=callback_url
            )
            
            # Prepare response data
            response_data = {
                'reference': payment.reference,
                'authorization_url': payment.authorization_url,
                'access_code': payment.access_code,
                'amount': payment.amount_in_naira,
                'customer_email': payment.customer_email,
                'status': payment.status,
                'created_at': payment.created_at
            }
            
            logger.info(f"Payment initialized successfully: {payment.reference}")
            
            return Response(
                response_data,
                status=status.HTTP_201_CREATED
            )
            
        except PaystackAPIError as e:
            logger.error(f"Paystack API error: {str(e)}")
            return Response(
                {
                    'error': 'Payment initialization failed',
                    'details': {'message': str(e)},
                    'timestamp': timezone.now()
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error in payment initialization: {str(e)}")
            return Response(
                {
                    'error': 'Internal server error',
                    'details': {'message': 'Payment initialization failed'},
                    'timestamp': timezone.now()
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class PaymentWebhookView(APIView):
    """
    Handle Paystack webhook notifications.
    
    This endpoint processes webhook events from Paystack, verifies signatures,
    and updates payment records accordingly.
    """
    
    permission_classes = [AllowAny]
    
    @extend_schema(
        operation_id='payment_webhook',
        summary='Paystack Webhook Handler',
        description='Handle webhook notifications from Paystack',
        request=WebhookEventSerializer,
        responses={
            200: OpenApiResponse(description='Webhook processed successfully'),
            403: OpenApiResponse(description='Invalid webhook signature'),
            500: OpenApiResponse(description='Webhook processing failed')
        }
    )
    def post(self, request):
        """Process Paystack webhook events"""
        
        # Get the raw payload for signature verification
        try:
            payload = request.body
            signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE')
            
            if not signature:
                logger.warning("Missing x-paystack-signature header")
                return HttpResponse(
                    'Missing signature header',
                    status=403
                )
            
            # Verify webhook signature
            payment_service = PaymentService()
            if not payment_service.paystack.verify_webhook_signature(payload, signature):
                logger.warning("Invalid webhook signature")
                return HttpResponse(
                    'Invalid signature',
                    status=403
                )
            
            # Parse webhook data
            webhook_data = json.loads(payload.decode('utf-8'))
            event_type = webhook_data.get('event')
            event_data = webhook_data.get('data', {})
            
            logger.info(f"Processing webhook event: {event_type}")
            
            # Process charge.success events
            if event_type == 'charge.success':
                reference = event_data.get('reference')
                
                if not reference:
                    logger.error("Missing reference in webhook data")
                    return HttpResponse(
                        'Missing reference in webhook data',
                        status=400
                    )
                
                # Process the payment in a database transaction
                try:
                    with transaction.atomic():
                        payment = payment_service.process_webhook_payment(
                            reference=reference,
                            webhook_data=event_data
                        )
                        
                        if payment:
                            logger.info(f"Webhook processed successfully: {reference}")
                        else:
                            logger.warning(f"Payment not found for webhook: {reference}")
                            
                except Exception as e:
                    logger.error(f"Error processing webhook: {str(e)}")
                    return HttpResponse(
                        'Processing failed',
                        status=500
                    )
            
            else:
                logger.info(f"Ignoring webhook event: {event_type}")
            
            return HttpResponse('OK', status=200)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook payload: {str(e)}")
            return HttpResponse(
                'Invalid JSON payload',
                status=400
            )
        except Exception as e:
            logger.error(f"Unexpected error processing webhook: {str(e)}")
            return HttpResponse(
                'Internal server error',
                status=500
            )


class PaymentVerifyView(APIView):
    """
    Verify a payment transaction with Paystack.
    
    This endpoint allows manual verification of payment status
    by calling the Paystack verify endpoint.
    """
    
    permission_classes = [AllowAny]
    
    @extend_schema(
        operation_id='verify_payment',
        summary='Verify Payment',
        description='Verify payment status with Paystack API',
        parameters=[
            OpenApiParameter(
                name='reference',
                description='Payment reference to verify',
                required=True,
                type=str,
                location=OpenApiParameter.PATH
            )
        ],
        responses={
            200: OpenApiResponse(
                response=PaymentVerificationResponseSerializer,
                description='Payment verification successful'
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Payment not found'
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Verification failed'
            )
        }
    )
    def get(self, request, reference):
        """Verify a payment transaction"""
        
        try:
            # Get payment from database
            payment = Payment.objects.get(reference=reference)
            
            # Verify with Paystack
            payment_service = PaymentService()
            verification_data = payment_service.paystack.verify_transaction(reference)
            
            # Update payment record
            with transaction.atomic():
                payment = Payment.objects.select_for_update().get(reference=reference)
                
                # Update paystack response
                payment.paystack_response['verification'] = verification_data
                
                # Update payment status based on verification
                paystack_status = verification_data.get('status')
                if paystack_status == 'success' and payment.status != 'success':
                    payment.mark_as_paid()
                    
                    # Update user profile
                    if hasattr(payment.user, 'profile'):
                        payment.user.profile.payment_status = 'completed'
                        payment.user.profile.save()
                        
                elif paystack_status == 'failed':
                    payment.mark_as_failed(f"Paystack status: {paystack_status}")
                
                payment.save()
            
            # Prepare response
            response_data = {
                'reference': payment.reference,
                'status': payment.status,
                'amount': payment.amount,
                'currency': payment.currency,
                'customer_email': payment.customer_email,
                'paid_at': payment.paid_at,
                'verification_data': verification_data
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Payment.DoesNotExist:
            return Response(
                {
                    'error': 'Payment not found',
                    'details': {'reference': reference},
                    'timestamp': timezone.now()
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except PaystackAPIError as e:
            logger.error(f"Paystack verification error: {str(e)}")
            return Response(
                {
                    'error': 'Payment verification failed',
                    'details': {'message': str(e)},
                    'timestamp': timezone.now()
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error in payment verification: {str(e)}")
            return Response(
                {
                    'error': 'Internal server error',
                    'details': {'message': 'Verification failed'},
                    'timestamp': timezone.now()
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentCallbackView(APIView):
    """
    Handle payment callback redirects from Paystack.
    
    This endpoint handles the optional redirect callback from Paystack
    after payment completion.
    """
    
    permission_classes = [AllowAny]
    
    @extend_schema(
        operation_id='payment_callback',
        summary='Payment Callback Handler',
        description='Handle payment completion callback from Paystack',
        parameters=[
            OpenApiParameter(
                name='reference',
                description='Payment reference',
                required=True,
                type=str,
                location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name='trxref',
                description='Transaction reference (optional)',
                required=False,
                type=str,
                location=OpenApiParameter.QUERY
            )
        ],
        responses={
            200: OpenApiResponse(description='Callback processed successfully'),
            404: OpenApiResponse(description='Payment not found')
        }
    )
    def get(self, request):
        """Handle payment callback"""
        
        serializer = PaymentCallbackSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'Invalid callback parameters',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reference = serializer.validated_data['reference']
        
        try:
            payment = Payment.objects.get(reference=reference)
            
            # Log callback received
            logger.info(f"Payment callback received: {reference}")
            
            response_data = {
                'reference': payment.reference,
                'status': payment.status,
                'amount': payment.amount_in_naira,
                'customer_email': payment.customer_email,
                'message': 'Callback received successfully'
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Payment.DoesNotExist:
            return Response(
                {
                    'error': 'Payment not found',
                    'details': {'reference': reference}
                },
                status=status.HTTP_404_NOT_FOUND
            )


class PaymentListView(ListAPIView):
    """
    List all payments with optional filtering.
    """
    
    serializer_class = PaymentListSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        operation_id='list_payments',
        summary='List Payments',
        description='Get a list of all payments with optional filtering',
        parameters=[
            OpenApiParameter(
                name='status',
                description='Filter by payment status',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='email',
                description='Filter by customer email',
                required=False,
                type=str
            )
        ]
    )
    def get_queryset(self):
        """Get filtered payment queryset"""
        queryset = Payment.objects.select_related('user').order_by('-created_at')
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by email
        email_filter = self.request.query_params.get('email')
        if email_filter:
            queryset = queryset.filter(customer_email__icontains=email_filter)
        
        return queryset


class PaymentDetailView(RetrieveAPIView):
    """
    Get detailed information about a specific payment.
    """
    
    serializer_class = PaymentDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'reference'
    
    @extend_schema(
        operation_id='get_payment_detail',
        summary='Get Payment Details',
        description='Get detailed information about a specific payment'
    )
    def get_queryset(self):
        """Get payment queryset with related data"""
        return Payment.objects.select_related('user')
