"""
Unit tests for payment services and Paystack integration.
"""

import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings

from ..services import PaystackService, PaymentService, PaystackAPIError
from ..models import Payment, UserProfile


class PaystackServiceTest(TestCase):
    """Tests for PaystackService"""
    
    def setUp(self):
        self.service = PaystackService()
        self.test_payload = {
            'email': 'test@example.com',
            'amount': 10000,
            'reference': 'TEST_REF_123'
        }
    
    def test_service_initialization(self):
        """Test that service initializes with correct keys"""
        self.assertEqual(self.service.secret_key, settings.PAYSTACK_SECRET_KEY)
        self.assertEqual(self.service.public_key, settings.PAYSTACK_PUBLIC_KEY)
        self.assertEqual(self.service.base_url, settings.PAYSTACK_BASE_URL)
    
    def test_get_headers(self):
        """Test that headers are generated correctly"""
        headers = self.service._get_headers()
        expected_headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        self.assertEqual(headers, expected_headers)
    
    @patch('requests.request')
    def test_make_request_success(self, mock_request):
        """Test successful API request"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'status': True,
            'data': {'test': 'data'}
        }
        mock_request.return_value = mock_response
        
        result = self.service._make_request('POST', '/test/endpoint', {'test': 'data'})
        
        self.assertTrue(result['status'])
        self.assertEqual(result['data']['test'], 'data')
        mock_request.assert_called_once()
    
    @patch('requests.request')
    def test_make_request_api_error(self, mock_request):
        """Test API error handling"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'status': False,
            'message': 'API Error occurred'
        }
        mock_request.return_value = mock_response
        
        with self.assertRaises(PaystackAPIError) as context:
            self.service._make_request('POST', '/test/endpoint', {'test': 'data'})
        
        self.assertIn('API Error occurred', str(context.exception))
    
    @patch('requests.request')
    def test_make_request_http_error(self, mock_request):
        """Test HTTP error handling"""
        mock_request.side_effect = Exception('Connection error')
        
        with self.assertRaises(PaystackAPIError) as context:
            self.service._make_request('POST', '/test/endpoint', {'test': 'data'})
        
        self.assertIn('Connection error', str(context.exception))
    
    @patch.object(PaystackService, '_make_request')
    def test_initialize_transaction_success(self, mock_make_request):
        """Test successful transaction initialization"""
        mock_make_request.return_value = {
            'authorization_url': 'https://checkout.paystack.com/test123',
            'access_code': 'test_access_code',
            'reference': 'TEST_REF_123'
        }
        
        result = self.service.initialize_transaction(
            email='test@example.com',
            amount_in_kobo=10000,
            reference='TEST_REF_123'
        )
        
        self.assertEqual(result['authorization_url'], 'https://checkout.paystack.com/test123')
        self.assertEqual(result['access_code'], 'test_access_code')
        mock_make_request.assert_called_once()
    
    @patch.object(PaystackService, '_make_request')
    def test_verify_transaction_success(self, mock_make_request):
        """Test successful transaction verification"""
        mock_make_request.return_value = {
            'status': 'success',
            'reference': 'TEST_REF_123',
            'amount': 10000,
            'currency': 'NGN'
        }
        
        result = self.service.verify_transaction('TEST_REF_123')
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['reference'], 'TEST_REF_123')
        mock_make_request.assert_called_once_with('GET', '/transaction/verify/TEST_REF_123')
    
    def test_verify_webhook_signature_valid(self):
        """Test valid webhook signature verification"""
        payload = b'{"event": "charge.success", "data": {"reference": "test"}}'
        
        # Create valid signature
        expected_signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        result = self.service.verify_webhook_signature(payload, expected_signature)
        self.assertTrue(result)
    
    def test_verify_webhook_signature_invalid(self):
        """Test invalid webhook signature verification"""
        payload = b'{"event": "charge.success", "data": {"reference": "test"}}'
        invalid_signature = 'invalid_signature_123'
        
        result = self.service.verify_webhook_signature(payload, invalid_signature)
        self.assertFalse(result)
    
    def test_verify_webhook_signature_exception(self):
        """Test webhook signature verification with exception"""
        result = self.service.verify_webhook_signature(None, 'signature')
        self.assertFalse(result)


class PaymentServiceTest(TestCase):
    """Tests for PaymentService"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.service = PaymentService()
    
    def test_generate_reference(self):
        """Test reference generation"""
        reference = PaymentService.generate_reference()
        
        self.assertTrue(reference.startswith('PAY_'))
        self.assertEqual(len(reference), 27)  # PAY_ + 14 digits + _ + 8 chars
    
    def test_generate_reference_uniqueness(self):
        """Test that generated references are unique"""
        refs = [PaymentService.generate_reference() for _ in range(10)]
        self.assertEqual(len(refs), len(set(refs)))  # All should be unique
    
    @patch.object(PaystackService, 'initialize_transaction')
    def test_create_payment_success(self, mock_initialize):
        """Test successful payment creation"""
        mock_paystack_data = {
            'authorization_url': 'https://checkout.paystack.com/test123',
            'access_code': 'test_access_code',
            'reference': 'PAY_20240122123456_ABC12345'
        }
        mock_initialize.return_value = mock_paystack_data
        
        payment, paystack_data = self.service.create_payment(
            user=self.user,
            customer_email='customer@example.com',
            amount_naira=Decimal('100.00')
        )
        
        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.customer_email, 'customer@example.com')
        self.assertEqual(payment.amount, Decimal('10000'))  # 100 NGN in kobo
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(paystack_data, mock_paystack_data)
    
    @patch.object(PaystackService, 'initialize_transaction')
    def test_create_payment_paystack_error(self, mock_initialize):
        """Test payment creation with Paystack error"""
        mock_initialize.side_effect = PaystackAPIError('Paystack API error')
        
        with self.assertRaises(PaystackAPIError):
            self.service.create_payment(
                user=self.user,
                customer_email='customer@example.com',
                amount_naira=Decimal('100.00')
            )
    
    def test_process_webhook_payment_success(self):
        """Test successful webhook payment processing"""
        # Create a payment first
        payment = Payment.objects.create(
            user=self.user,
            reference='TEST_REF_123',
            customer_email='customer@example.com',
            amount=Decimal('10000'),
            status='pending'
        )
        
        webhook_data = {
            'reference': 'TEST_REF_123',
            'status': 'success',
            'amount': 10000
        }
        
        with patch.object(PaystackService, 'verify_transaction') as mock_verify:
            mock_verify.return_value = {
                'status': 'success',
                'reference': 'TEST_REF_123',
                'amount': 10000
            }
            
            result = self.service.process_webhook_payment('TEST_REF_123', webhook_data)
            
            self.assertIsNotNone(result)
            self.assertEqual(result.status, 'success')
            self.assertTrue(result.webhook_received)
            self.assertTrue(result.webhook_verified)
    
    def test_process_webhook_payment_not_found(self):
        """Test webhook processing for non-existent payment"""
        webhook_data = {'reference': 'NONEXISTENT_REF', 'status': 'success'}
        
        result = self.service.process_webhook_payment('NONEXISTENT_REF', webhook_data)
        self.assertIsNone(result)
    
    @patch.object(PaystackService, 'verify_transaction')
    def test_process_webhook_payment_verification_failed(self, mock_verify):
        """Test webhook processing with verification failure"""
        payment = Payment.objects.create(
            user=self.user,
            reference='TEST_REF_456',
            customer_email='customer@example.com',
            amount=Decimal('10000'),
            status='pending'
        )
        
        mock_verify.return_value = {
            'status': 'failed',
            'reference': 'TEST_REF_456'
        }
        
        webhook_data = {'reference': 'TEST_REF_456', 'status': 'success'}
        result = self.service.process_webhook_payment('TEST_REF_456', webhook_data)
        
        result.refresh_from_db()
        self.assertEqual(result.status, 'failed')
    
    @patch.object(PaystackService, 'verify_transaction')
    def test_process_webhook_payment_api_error(self, mock_verify):
        """Test webhook processing with Paystack API error"""
        payment = Payment.objects.create(
            user=self.user,
            reference='TEST_REF_789',
            customer_email='customer@example.com',
            amount=Decimal('10000'),
            status='pending'
        )
        
        mock_verify.side_effect = PaystackAPIError('API error')
        
        webhook_data = {'reference': 'TEST_REF_789', 'status': 'success'}
        result = self.service.process_webhook_payment('TEST_REF_789', webhook_data)
        
        result.refresh_from_db()
        self.assertEqual(result.status, 'failed')
        self.assertIn('Verification failed', result.metadata.get('failure_reason', ''))


class PaymentServiceIntegrationTest(TestCase):
    """Integration tests for PaymentService"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.service = PaymentService()
    
    @patch('requests.request')
    def test_end_to_end_payment_flow(self, mock_request):
        """Test complete payment flow from initialization to completion"""
        # Mock Paystack initialization response
        mock_init_response = Mock()
        mock_init_response.raise_for_status.return_value = None
        mock_init_response.json.return_value = {
            'status': True,
            'data': {
                'authorization_url': 'https://checkout.paystack.com/test123',
                'access_code': 'test_access_code',
                'reference': 'PAY_TEST_REF'
            }
        }
        
        # Mock Paystack verification response
        mock_verify_response = Mock()
        mock_verify_response.raise_for_status.return_value = None
        mock_verify_response.json.return_value = {
            'status': True,
            'data': {
                'status': 'success',
                'reference': 'PAY_TEST_REF',
                'amount': 10000,
                'currency': 'NGN'
            }
        }
        
        mock_request.side_effect = [mock_init_response, mock_verify_response]
        
        # Step 1: Create payment
        with patch.object(PaymentService, 'generate_reference') as mock_ref:
            mock_ref.return_value = 'PAY_TEST_REF'
            
            payment, paystack_data = self.service.create_payment(
                user=self.user,
                customer_email='customer@example.com',
                amount_naira=Decimal('100.00')
            )
        
        # Verify payment creation
        self.assertEqual(payment.reference, 'PAY_TEST_REF')
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(payment.amount, Decimal('10000'))
        
        # Step 2: Process webhook (simulate payment completion)
        webhook_data = {
            'event': 'charge.success',
            'data': {
                'reference': 'PAY_TEST_REF',
                'status': 'success',
                'amount': 10000
            }
        }
        
        result = self.service.process_webhook_payment(
            'PAY_TEST_REF', 
            webhook_data['data']
        )
        
        # Verify payment completion
        self.assertEqual(result.status, 'success')
        self.assertTrue(result.webhook_received)
        self.assertTrue(result.webhook_verified)
        self.assertIsNotNone(result.paid_at)