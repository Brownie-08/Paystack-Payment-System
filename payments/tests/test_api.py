"""
Integration tests for payment API endpoints.
"""

import json
import hashlib
import hmac
from decimal import Decimal
from unittest.mock import patch, Mock

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from rest_framework import status
from rest_framework.test import APIClient

from ..models import Payment, UserProfile
from ..services import PaystackAPIError


class PaymentAPITestCase(TestCase):
    """Base test case for payment API tests"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test payment data
        self.payment_data = {
            'email': 'customer@example.com',
            'amount': '100.00',
            'callback_url': 'https://example.com/callback'
        }
        
        # Mock Paystack responses
        self.mock_paystack_init_response = {
            'authorization_url': 'https://checkout.paystack.com/test123',
            'access_code': 'test_access_code',
            'reference': 'PAY_TEST_REF_123'
        }


class PaymentInitializeAPITest(PaymentAPITestCase):
    """Tests for payment initialization API"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('payments:payment-initiate')
    
    @patch('payments.services.PaystackService.initialize_transaction')
    def test_initialize_payment_success(self, mock_initialize):
        """Test successful payment initialization"""
        mock_initialize.return_value = self.mock_paystack_init_response
        
        response = self.client.post(self.url, self.payment_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('reference', response.data)
        self.assertIn('authorization_url', response.data)
        self.assertIn('access_code', response.data)
        
        # Verify payment was created in database
        payment = Payment.objects.get(reference=response.data['reference'])
        self.assertEqual(payment.customer_email, 'customer@example.com')
        self.assertEqual(payment.amount, Decimal('10000'))  # 100 NGN in kobo
    
    def test_initialize_payment_invalid_data(self):
        """Test payment initialization with invalid data"""
        invalid_data = {
            'email': 'invalid-email',
            'amount': 'invalid-amount'
        }
        
        response = self.client.post(self.url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('details', response.data)
    
    def test_initialize_payment_missing_email(self):
        """Test payment initialization without email"""
        data = {
            'amount': '100.00'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data['details'])
    
    def test_initialize_payment_minimum_amount(self):
        """Test payment initialization with amount below minimum"""
        data = {
            'email': 'test@example.com',
            'amount': '0.50'  # Below minimum of 1.00
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_initialize_payment_maximum_amount(self):
        """Test payment initialization with amount above maximum"""
        data = {
            'email': 'test@example.com',
            'amount': '1000001.00'  # Above maximum of 1,000,000
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('payments.services.PaystackService.initialize_transaction')
    def test_initialize_payment_paystack_error(self, mock_initialize):
        """Test payment initialization with Paystack API error"""
        mock_initialize.side_effect = PaystackAPIError('Paystack API error')
        
        response = self.client.post(self.url, self.payment_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
        self.assertIn('Payment initialization failed', response.data['error'])


class PaymentWebhookAPITest(PaymentAPITestCase):
    """Tests for payment webhook API"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('payments:payment-webhook')
        self.payment = Payment.objects.create(
            user=self.user,
            reference='TEST_WEBHOOK_REF',
            customer_email='customer@example.com',
            amount=Decimal('10000'),
            status='pending'
        )
        
        self.webhook_payload = {
            'event': 'charge.success',
            'data': {
                'reference': 'TEST_WEBHOOK_REF',
                'status': 'success',
                'amount': 10000,
                'currency': 'NGN'
            }
        }
    
    def _generate_valid_signature(self, payload):
        """Generate valid webhook signature"""
        payload_bytes = json.dumps(payload).encode('utf-8')
        signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            payload_bytes,
            hashlib.sha512
        ).hexdigest()
        return signature
    
    @patch('payments.services.PaystackService.verify_transaction')
    def test_webhook_charge_success(self, mock_verify):
        """Test successful webhook processing"""
        mock_verify.return_value = {
            'status': 'success',
            'reference': 'TEST_WEBHOOK_REF',
            'amount': 10000
        }
        
        payload = json.dumps(self.webhook_payload)
        signature = self._generate_valid_signature(self.webhook_payload)
        
        response = self.client.post(
            self.url,
            payload,
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE=signature
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'OK')
        
        # Verify payment was updated
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'success')
        self.assertTrue(self.payment.webhook_received)
        self.assertTrue(self.payment.webhook_verified)
    
    def test_webhook_invalid_signature(self):
        """Test webhook with invalid signature"""
        payload = json.dumps(self.webhook_payload)
        invalid_signature = 'invalid_signature_123'
        
        response = self.client.post(
            self.url,
            payload,
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE=invalid_signature
        )
        
        self.assertEqual(response.status_code, 403)
    
    def test_webhook_missing_signature(self):
        \"\"\"Test webhook without signature header\"\"\"\n        payload = json.dumps(self.webhook_payload)\n        \n        response = self.client.post(\n            self.url,\n            payload,\n            content_type='application/json'\n        )\n        \n        self.assertEqual(response.status_code, 403)\n    \n    def test_webhook_invalid_json(self):\n        \"\"\"Test webhook with invalid JSON payload\"\"\"\n        invalid_payload = '{invalid json}'\n        signature = self._generate_valid_signature({'test': 'data'})\n        \n        response = self.client.post(\n            self.url,\n            invalid_payload,\n            content_type='application/json',\n            HTTP_X_PAYSTACK_SIGNATURE=signature\n        )\n        \n        self.assertEqual(response.status_code, 400)\n    \n    @patch('payments.services.PaystackService.verify_transaction')\n    def test_webhook_payment_not_found(self, mock_verify):\n        \"\"\"Test webhook for non-existent payment\"\"\"\n        webhook_payload = {\n            'event': 'charge.success',\n            'data': {\n                'reference': 'NONEXISTENT_REF',\n                'status': 'success',\n                'amount': 10000\n            }\n        }\n        \n        payload = json.dumps(webhook_payload)\n        signature = self._generate_valid_signature(webhook_payload)\n        \n        response = self.client.post(\n            self.url,\n            payload,\n            content_type='application/json',\n            HTTP_X_PAYSTACK_SIGNATURE=signature\n        )\n        \n        self.assertEqual(response.status_code, 200)  # Should still return OK\n    \n    def test_webhook_unsupported_event(self):\n        \"\"\"Test webhook with unsupported event type\"\"\"\n        webhook_payload = {\n            'event': 'unsupported.event',\n            'data': {}\n        }\n        \n        payload = json.dumps(webhook_payload)\n        signature = self._generate_valid_signature(webhook_payload)\n        \n        response = self.client.post(\n            self.url,\n            payload,\n            content_type='application/json',\n            HTTP_X_PAYSTACK_SIGNATURE=signature\n        )\n        \n        self.assertEqual(response.status_code, 200)  # Should return OK but ignore event\n\n\nclass PaymentVerifyAPITest(PaymentAPITestCase):\n    \"\"\"Tests for payment verification API\"\"\"\n    \n    def setUp(self):\n        super().setUp()\n        self.payment = Payment.objects.create(\n            user=self.user,\n            reference='TEST_VERIFY_REF',\n            customer_email='customer@example.com',\n            amount=Decimal('10000'),\n            status='pending'\n        )\n        self.url = reverse('payments:payment-verify', kwargs={'reference': 'TEST_VERIFY_REF'})\n    \n    @patch('payments.services.PaystackService.verify_transaction')\n    def test_verify_payment_success(self, mock_verify):\n        \"\"\"Test successful payment verification\"\"\"\n        mock_verify.return_value = {\n            'status': 'success',\n            'reference': 'TEST_VERIFY_REF',\n            'amount': 10000,\n            'currency': 'NGN'\n        }\n        \n        response = self.client.get(self.url)\n        \n        self.assertEqual(response.status_code, status.HTTP_200_OK)\n        self.assertEqual(response.data['reference'], 'TEST_VERIFY_REF')\n        self.assertEqual(response.data['status'], 'success')\n        \n        # Verify payment was updated\n        self.payment.refresh_from_db()\n        self.assertEqual(self.payment.status, 'success')\n    \n    def test_verify_payment_not_found(self):\n        \"\"\"Test verification of non-existent payment\"\"\"\n        url = reverse('payments:payment-verify', kwargs={'reference': 'NONEXISTENT_REF'})\n        response = self.client.get(url)\n        \n        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)\n        self.assertIn('error', response.data)\n    \n    @patch('payments.services.PaystackService.verify_transaction')\n    def test_verify_payment_paystack_error(self, mock_verify):\n        \"\"\"Test payment verification with Paystack API error\"\"\"\n        mock_verify.side_effect = PaystackAPIError('API error')\n        \n        response = self.client.get(self.url)\n        \n        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)\n        self.assertIn('error', response.data)\n\n\nclass PaymentCallbackAPITest(PaymentAPITestCase):\n    \"\"\"Tests for payment callback API\"\"\"\n    \n    def setUp(self):\n        super().setUp()\n        self.payment = Payment.objects.create(\n            user=self.user,\n            reference='TEST_CALLBACK_REF',\n            customer_email='customer@example.com',\n            amount=Decimal('10000'),\n            status='pending'\n        )\n        self.url = reverse('payments:payment-callback')\n    \n    def test_payment_callback_success(self):\n        \"\"\"Test successful payment callback\"\"\"\n        response = self.client.get(self.url, {'reference': 'TEST_CALLBACK_REF'})\n        \n        self.assertEqual(response.status_code, status.HTTP_200_OK)\n        self.assertEqual(response.data['reference'], 'TEST_CALLBACK_REF')\n        self.assertIn('message', response.data)\n    \n    def test_payment_callback_missing_reference(self):\n        \"\"\"Test callback without reference parameter\"\"\"\n        response = self.client.get(self.url)\n        \n        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)\n        self.assertIn('error', response.data)\n    \n    def test_payment_callback_not_found(self):\n        \"\"\"Test callback for non-existent payment\"\"\"\n        response = self.client.get(self.url, {'reference': 'NONEXISTENT_REF'})\n        \n        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)\n        self.assertIn('error', response.data)\n\n\nclass PaymentListAPITest(PaymentAPITestCase):\n    \"\"\"Tests for payment list API\"\"\"\n    \n    def setUp(self):\n        super().setUp()\n        self.url = reverse('payments:payment-list')\n        \n        # Create multiple payments for testing\n        self.payment1 = Payment.objects.create(\n            user=self.user,\n            reference='TEST_LIST_REF_1',\n            customer_email='customer1@example.com',\n            amount=Decimal('10000'),\n            status='pending'\n        )\n        \n        self.payment2 = Payment.objects.create(\n            user=self.user,\n            reference='TEST_LIST_REF_2',\n            customer_email='customer2@example.com',\n            amount=Decimal('20000'),\n            status='success'\n        )\n    \n    def test_payment_list_all(self):\n        \"\"\"Test getting all payments\"\"\"\n        response = self.client.get(self.url)\n        \n        self.assertEqual(response.status_code, status.HTTP_200_OK)\n        self.assertEqual(len(response.data), 2)\n    \n    def test_payment_list_filter_by_status(self):\n        \"\"\"Test filtering payments by status\"\"\"\n        response = self.client.get(self.url, {'status': 'success'})\n        \n        self.assertEqual(response.status_code, status.HTTP_200_OK)\n        self.assertEqual(len(response.data), 1)\n        self.assertEqual(response.data[0]['reference'], 'TEST_LIST_REF_2')\n    \n    def test_payment_list_filter_by_email(self):\n        \"\"\"Test filtering payments by email\"\"\"\n        response = self.client.get(self.url, {'email': 'customer1@example.com'})\n        \n        self.assertEqual(response.status_code, status.HTTP_200_OK)\n        self.assertEqual(len(response.data), 1)\n        self.assertEqual(response.data[0]['reference'], 'TEST_LIST_REF_1')\n\n\nclass PaymentDetailAPITest(PaymentAPITestCase):\n    \"\"\"Tests for payment detail API\"\"\"\n    \n    def setUp(self):\n        super().setUp()\n        self.payment = Payment.objects.create(\n            user=self.user,\n            reference='TEST_DETAIL_REF',\n            customer_email='customer@example.com',\n            amount=Decimal('15000'),\n            status='success',\n            metadata={'source': 'web'}\n        )\n        self.url = reverse('payments:payment-detail', kwargs={'reference': 'TEST_DETAIL_REF'})\n    \n    def test_payment_detail_success(self):\n        \"\"\"Test getting payment details\"\"\"\n        response = self.client.get(self.url)\n        \n        self.assertEqual(response.status_code, status.HTTP_200_OK)\n        self.assertEqual(response.data['reference'], 'TEST_DETAIL_REF')\n        self.assertEqual(response.data['status'], 'success')\n        self.assertEqual(response.data['metadata']['source'], 'web')\n        self.assertIn('user_email', response.data)\n    \n    def test_payment_detail_not_found(self):\n        \"\"\"Test getting details for non-existent payment\"\"\"\n        url = reverse('payments:payment-detail', kwargs={'reference': 'NONEXISTENT_REF'})\n        response = self.client.get(url)\n        \n        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)