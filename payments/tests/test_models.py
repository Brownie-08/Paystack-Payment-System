"""
Unit tests for payment models.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils import timezone

from ..models import Payment, UserProfile


class UserProfileModelTest(TestCase):
    """Tests for UserProfile model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_profile_creation(self):
        """Test that UserProfile is created with proper defaults"""
        # Profile should already exist due to signals
        profile = self.user.profile
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.payment_status, 'pending')
        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.updated_at)
    
    def test_user_profile_str_method(self):
        """Test UserProfile string representation"""
        profile = self.user.profile
        expected_str = f"{self.user.email} (Pending)"
        self.assertEqual(str(profile), expected_str)
    
    def test_user_profile_payment_status_choices(self):
        """Test that all payment status choices work"""
        profile = self.user.profile
        
        valid_statuses = ['pending', 'completed', 'failed', 'refunded']
        for status in valid_statuses:
            profile.payment_status = status
            profile.save()
            profile.refresh_from_db()
            self.assertEqual(profile.payment_status, status)
    
    def test_one_to_one_relationship(self):
        """Test that one user can have only one profile"""
        # Profile already exists due to signals
        self.assertTrue(hasattr(self.user, 'profile'))
        
        # Trying to create another should fail
        with self.assertRaises(IntegrityError):
            UserProfile.objects.create(user=self.user)


class PaymentModelTest(TestCase):
    """Tests for Payment model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.payment_data = {
            'user': self.user,
            'reference': 'TEST_REF_123',
            'customer_email': 'customer@example.com',
            'amount': Decimal('10000'),  # 100 NGN in kobo
            'currency': 'NGN',
        }
    
    def test_payment_creation(self):
        """Test basic payment creation"""
        payment = Payment.objects.create(**self.payment_data)
        
        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.reference, 'TEST_REF_123')
        self.assertEqual(payment.customer_email, 'customer@example.com')
        self.assertEqual(payment.amount, Decimal('10000'))
        self.assertEqual(payment.currency, 'NGN')
        self.assertEqual(payment.status, 'pending')
        self.assertIsNotNone(payment.created_at)
        self.assertIsNotNone(payment.updated_at)
        self.assertIsNone(payment.paid_at)
    
    def test_payment_str_method(self):
        """Test Payment string representation"""
        payment = Payment.objects.create(**self.payment_data)
        expected_str = f"Payment TEST_REF_123 - Pending - ₦100.0"
        self.assertEqual(str(payment), expected_str)
    
    def test_amount_in_naira_property(self):
        """Test conversion from kobo to naira"""
        payment = Payment.objects.create(**self.payment_data)
        self.assertEqual(payment.amount_in_naira, 100.0)
    
    def test_naira_to_kobo_class_method(self):
        """Test conversion from naira to kobo"""
        naira_amount = Decimal('100.50')
        kobo_amount = Payment.naira_to_kobo(naira_amount)
        self.assertEqual(kobo_amount, Decimal('10050'))
    
    def test_unique_reference_constraint(self):
        """Test that payment reference must be unique"""
        Payment.objects.create(**self.payment_data)
        
        with self.assertRaises(IntegrityError):
            Payment.objects.create(**self.payment_data)
    
    def test_mark_as_paid_method(self):
        """Test marking payment as successful"""
        payment = Payment.objects.create(**self.payment_data)
        payment.mark_as_paid()
        
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'success')
        self.assertTrue(payment.webhook_verified)
        self.assertIsNotNone(payment.paid_at)
    
    def test_mark_as_failed_method(self):
        """Test marking payment as failed"""
        payment = Payment.objects.create(**self.payment_data)
        reason = "Insufficient funds"
        payment.mark_as_failed(reason)
        
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'failed')
        self.assertEqual(payment.metadata['failure_reason'], reason)
    
    def test_payment_status_choices(self):
        """Test that all payment status choices work"""
        payment = Payment.objects.create(**self.payment_data)
        
        valid_statuses = ['pending', 'processing', 'success', 'failed', 'cancelled', 'abandoned']
        for status in valid_statuses:
            payment.status = status
            payment.save()
            payment.refresh_from_db()
            self.assertEqual(payment.status, status)
    
    def test_amount_validation(self):
        """Test that amount validation works"""
        # Test minimum amount validation
        self.payment_data['amount'] = Decimal('0.50')  # Less than minimum
        payment = Payment(**self.payment_data)
        
        with self.assertRaises(ValidationError):
            payment.full_clean()
    
    def test_payment_metadata_default(self):
        """Test that metadata defaults to empty dict"""
        payment = Payment.objects.create(**self.payment_data)
        self.assertEqual(payment.metadata, {})
    
    def test_payment_paystack_response_default(self):
        """Test that paystack_response defaults to empty dict"""
        payment = Payment.objects.create(**self.payment_data)
        self.assertEqual(payment.paystack_response, {})


class PaymentModelMethodsTest(TestCase):
    """Tests for Payment model methods and properties"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.payment = Payment.objects.create(
            user=self.user,
            reference='TEST_REF_456',
            customer_email='customer@example.com',
            amount=Decimal('50000'),  # 500 NGN in kobo
            currency='NGN'
        )
    
    def test_payment_ordering(self):
        """Test that payments are ordered by created_at descending"""
        # Create another payment
        payment2 = Payment.objects.create(
            user=self.user,
            reference='TEST_REF_789',
            customer_email='customer2@example.com',
            amount=Decimal('25000'),
        )
        
        payments = Payment.objects.all()
        self.assertEqual(payments.first(), payment2)  # Most recent first
        self.assertEqual(payments.last(), self.payment)
    
    def test_payment_with_optional_fields(self):
        """Test payment creation with optional fields"""
        payment_data = {
            'user': self.user,
            'reference': 'TEST_REF_999',
            'customer_email': 'customer@example.com',
            'amount': Decimal('15000'),
            'authorization_url': 'https://checkout.paystack.com/test123',
            'access_code': 'test_access_code',
            'metadata': {'source': 'web', 'plan': 'premium'},
            'paystack_response': {'status': True, 'data': {}}
        }
        
        payment = Payment.objects.create(**payment_data)
        
        self.assertEqual(payment.authorization_url, 'https://checkout.paystack.com/test123')
        self.assertEqual(payment.access_code, 'test_access_code')
        self.assertEqual(payment.metadata['source'], 'web')
        self.assertTrue(payment.paystack_response['status'])