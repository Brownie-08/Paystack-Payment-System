"""
Paystack API integration service module.

This module handles all interactions with the Paystack API including:
- Payment initialization
- Transaction verification
- Webhook signature verification
"""

import hashlib
import hmac
import logging
import uuid
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple

import requests
from django.conf import settings
from django.utils import timezone

from .models import Payment

logger = logging.getLogger('payments')


class PaystackAPIError(Exception):
    """Custom exception for Paystack API errors"""
    pass


class PaystackService:
    """Service class for Paystack API operations"""
    
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.public_key = settings.PAYSTACK_PUBLIC_KEY
        self.base_url = settings.PAYSTACK_BASE_URL
        
        if not self.secret_key:
            raise ValueError("PAYSTACK_SECRET_KEY is not configured")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Paystack API requests"""
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
        }
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Paystack API with error handling
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request payload data
            
        Returns:
            dict: API response data
            
        Raises:
            PaystackAPIError: If API request fails
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        try:
            logger.info(f"Making {method} request to Paystack: {endpoint}")
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            if not response_data.get('status'):
                error_msg = response_data.get('message', 'Unknown Paystack API error')
                logger.error(f"Paystack API error: {error_msg}")
                raise PaystackAPIError(f"Paystack API error: {error_msg}")
            
            logger.info(f"Paystack API request successful: {endpoint}")
            return response_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request failed: {str(e)}")
            raise PaystackAPIError(f"HTTP request failed: {str(e)}")
        except ValueError as e:
            logger.error(f"Invalid JSON response: {str(e)}")
            raise PaystackAPIError(f"Invalid JSON response: {str(e)}")
    
    def initialize_transaction(
        self, 
        email: str, 
        amount_in_kobo: int, 
        reference: str,
        callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initialize a payment transaction with Paystack
        
        Args:
            email: Customer's email address
            amount_in_kobo: Amount in kobo (Nigerian currency subunit)
            reference: Unique payment reference
            callback_url: Optional callback URL for redirect
            
        Returns:
            dict: Paystack response containing authorization_url and access_code
            
        Raises:
            PaystackAPIError: If initialization fails
        """
        payload = {
            'email': email,
            'amount': amount_in_kobo,
            'reference': reference,
        }
        
        if callback_url:
            payload['callback_url'] = callback_url
        
        logger.info(f"Initializing Paystack transaction for {email}, amount: NGN{amount_in_kobo/100}")
        
        try:
            response = self._make_request('POST', '/transaction/initialize', payload)
            
            # Log success but redact sensitive data
            logger.info(f"Transaction initialized successfully: {reference}")
            
            return response['data']
            
        except PaystackAPIError as e:
            logger.error(f"Failed to initialize transaction {reference}: {str(e)}")
            raise
    
    def verify_transaction(self, reference: str) -> Dict[str, Any]:
        """
        Verify a transaction with Paystack
        
        Args:
            reference: Payment reference to verify
            
        Returns:
            dict: Transaction verification data
            
        Raises:
            PaystackAPIError: If verification fails
        """
        logger.info(f"Verifying transaction: {reference}")
        
        try:
            response = self._make_request('GET', f'/transaction/verify/{reference}')
            
            transaction_data = response['data']
            status = transaction_data.get('status')
            
            logger.info(f"Transaction verification result: {reference} - {status}")
            
            return transaction_data
            
        except PaystackAPIError as e:
            logger.error(f"Failed to verify transaction {reference}: {str(e)}")
            raise
    
    def verify_webhook_signature(
        self, 
        payload: bytes, 
        signature: str
    ) -> bool:
        """
        Verify webhook signature using HMAC SHA512
        
        Args:
            payload: Raw webhook payload bytes
            signature: x-paystack-signature header value
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        try:
            # Create HMAC SHA512 signature
            expected_signature = hmac.new(
                self.secret_key.encode('utf-8'),
                payload,
                hashlib.sha512
            ).hexdigest()
            
            # Use constant-time comparison to prevent timing attacks
            is_valid = hmac.compare_digest(expected_signature, signature)
            
            if is_valid:
                logger.info("Webhook signature verification successful")
            else:
                logger.warning("Webhook signature verification failed")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Webhook signature verification error: {str(e)}")
            return False


class PaymentService:
    """Service class for payment-related operations"""
    
    def __init__(self):
        self.paystack = PaystackService()
    
    @staticmethod
    def generate_reference() -> str:
        """Generate a unique payment reference"""
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4()).replace('-', '')[:8].upper()
        return f"PAY_{timestamp}_{unique_id}"
    
    def create_payment(
        self,
        user,
        customer_email: str,
        amount_naira: Decimal,
        callback_url: Optional[str] = None
    ) -> Tuple[Payment, Dict[str, Any]]:
        """
        Create a new payment and initialize with Paystack
        
        Args:
            user: Django User instance
            customer_email: Customer's email address
            amount_naira: Amount in Naira
            callback_url: Optional callback URL
            
        Returns:
            tuple: (Payment instance, Paystack response data)
            
        Raises:
            PaystackAPIError: If Paystack initialization fails
        """
        # Generate unique reference
        reference = self.generate_reference()
        
        # Convert Naira to kobo
        amount_kobo = Payment.naira_to_kobo(amount_naira)
        
        logger.info(f"Creating payment: {reference} for {customer_email}, amount: NGN{amount_naira}")
        
        try:
            # Initialize transaction with Paystack
            paystack_data = self.paystack.initialize_transaction(
                email=customer_email,
                amount_in_kobo=int(amount_kobo),
                reference=reference,
                callback_url=callback_url
            )
            
            # Create payment record
            payment = Payment.objects.create(
                user=user,
                reference=reference,
                customer_email=customer_email,
                amount=amount_kobo,
                authorization_url=paystack_data.get('authorization_url'),
                access_code=paystack_data.get('access_code'),
                paystack_response=paystack_data,
                status='pending'
            )
            
            logger.info(f"Payment created successfully: {payment.id}")
            
            return payment, paystack_data
            
        except PaystackAPIError as e:
            logger.error(f"Failed to create payment: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating payment: {str(e)}")
            raise PaystackAPIError(f"Failed to create payment: {str(e)}")
    
    def process_webhook_payment(
        self, 
        reference: str, 
        webhook_data: Dict[str, Any]
    ) -> Optional[Payment]:
        """
        Process a payment from webhook data
        
        Args:
            reference: Payment reference
            webhook_data: Webhook payload data
            
        Returns:
            Payment instance if successful, None if payment not found
        """
        try:
            # Get payment with select_for_update for concurrency safety
            payment = Payment.objects.select_for_update().get(reference=reference)
            
            logger.info(f"Processing webhook for payment: {reference} (current status: {payment.status})")
            
            # Update webhook status
            payment.webhook_received = True
            
            # Merge webhook data with existing paystack_response
            if payment.paystack_response:
                payment.paystack_response.update(webhook_data)
            else:
                payment.paystack_response = webhook_data
            
            # Verify transaction with Paystack API
            try:
                logger.info(f"Verifying transaction with Paystack API: {reference}")
                verification_data = self.paystack.verify_transaction(reference)
                payment.paystack_response['verification'] = verification_data
                
                paystack_status = verification_data.get('status')
                paystack_amount = verification_data.get('amount', 0)
                
                logger.info(f"Paystack verification result - Status: {paystack_status}, Amount: {paystack_amount}")
                
                # Check if payment is successful
                if paystack_status == 'success':
                    # Verify amount matches (amount is in kobo)
                    if int(paystack_amount) == int(payment.amount):
                        payment.mark_as_paid()
                        
                        # Update user's payment status
                        if hasattr(payment.user, 'profile'):
                            payment.user.profile.payment_status = 'completed'
                            payment.user.profile.save()
                            logger.info(f"Updated user profile for {payment.user.email} to completed")
                        
                        logger.info(f"✅ Payment processed successfully: {reference} - ₦{payment.amount_in_naira}")
                    else:
                        payment.mark_as_failed(f"Amount mismatch: expected {payment.amount}, got {paystack_amount}")
                        logger.error(f"❌ Amount mismatch for {reference}: expected {payment.amount}, got {paystack_amount}")
                        
                elif paystack_status == 'failed':
                    payment.mark_as_failed(f"Payment status: {paystack_status}")
                    logger.warning(f"❌ Payment failed: {reference} - {paystack_status}")
                    
                else:
                    logger.warning(f"⚠️ Unexpected payment status: {reference} - {paystack_status}")
                    # Don't mark as failed, might be processing
            
            except PaystackAPIError as e:
                logger.error(f"Failed to verify payment {reference}: {str(e)}")
                payment.mark_as_failed(f"Verification failed: {str(e)}")
            
            # Save the payment with updated webhook status
            payment.save()
            
            return payment
            
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for webhook: {reference}")
            return None
        except Exception as e:
            logger.error(f"Error processing webhook payment {reference}: {str(e)}")
            return None
