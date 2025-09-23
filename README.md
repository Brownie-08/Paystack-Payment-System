# Django Paystack Payment Integration

A comprehensive Django REST API application for integrating Paystack payment processing with robust webhook handling, secure transaction verification, and complete payment lifecycle management.

## 🚀 Features

- **Payment Initialization**: Create Paystack payment transactions with automatic reference generation
- **Webhook Processing**: Secure webhook handling with HMAC SHA512 signature verification  
- **Transaction Verification**: Server-side verification of payments via Paystack API
- **Idempotent Operations**: Prevent duplicate payment processing with proper database locking
- **Comprehensive Logging**: Structured logging with secret redaction for security
- **API Documentation**: Auto-generated OpenAPI documentation with drf-spectacular
- **Robust Testing**: 80%+ test coverage with unit and integration tests
- **Security First**: Environment-based configuration, input validation, and CORS protection

## 📋 Prerequisites

- **Python 3.13.3+**
- **PostgreSQL 12+** (for production)
- **Redis** (for rate limiting and caching)
- **Paystack Account** (Test/Live API keys)

## 🛠️ Installation

### 1. Clone and Setup Project

```powershell
# Clone the repository
git clone <repository-url>
cd Payment_App

# Create virtual environment  
python -m venv venv

# Activate virtual environment (Windows PowerShell)
venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
# Django Configuration
SECRET_KEY=your-super-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,*.ngrok.io

# Database Configuration (PostgreSQL)
DB_NAME=payment_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration for Caching
REDIS_URL=redis://127.0.0.1:6379/1

# Paystack Configuration
PAYSTACK_SECRET_KEY=sk_test_your_secret_key_here
PAYSTACK_PUBLIC_KEY=pk_test_your_public_key_here
PAYSTACK_BASE_URL=https://api.paystack.co

# Application URLs
FRONTEND_CALLBACK_URL=http://localhost:3000/payment/callback
BACKEND_WEBHOOK_URL=http://localhost:8000/api/payments/webhook/
```

### 3. Database Setup

#### For Development (SQLite)
```powershell
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

#### For Production (PostgreSQL)
```powershell
# Install PostgreSQL locally or use cloud service
# Update settings.py to use PostgreSQL configuration

# Create database
createdb payment_db

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 4. Redis Setup (Optional for Rate Limiting)

#### Windows
```powershell
# Install Redis using Windows Subsystem for Linux or Docker
# Or use Redis Cloud service for production

# Update settings.py cache configuration with your Redis URL
```

## 🏃‍♂️ Running the Application

```powershell
# Start development server
python manage.py runserver

# The API will be available at:
# - Main API: http://127.0.0.1:8000/api/payments/
# - Admin Panel: http://127.0.0.1:8000/admin/
# - API Documentation: http://127.0.0.1:8000/api/docs/
# - API Schema: http://127.0.0.1:8000/api/redoc/
```

## 📚 API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/payments/initiate/` | Initialize a new payment |
| POST | `/api/payments/webhook/` | Handle Paystack webhooks |
| GET | `/api/payments/verify/{reference}/` | Verify payment status |
| GET | `/api/payments/callback/` | Handle payment callback |
| GET | `/api/payments/` | List all payments |
| GET | `/api/payments/{reference}/` | Get payment details |

### Payment Initialization

**POST** `/api/payments/initiate/`

```json
{
  "email": "customer@example.com",
  "amount": "1000.00",
  "callback_url": "https://yourapp.com/callback"
}
```

**Response:**
```json
{
  "reference": "PAY_20240122123456_ABC12345",
  "authorization_url": "https://checkout.paystack.com/xyz123",
  "access_code": "xyz123abc",
  "amount": "1000.00",
  "customer_email": "customer@example.com",
  "status": "pending",
  "created_at": "2024-01-22T12:34:56Z"
}
```

### Webhook Handling

**POST** `/api/payments/webhook/`

Paystack sends webhooks with the `x-paystack-signature` header. The endpoint:
1. Verifies the webhook signature using HMAC SHA512
2. Processes `charge.success` events
3. Updates payment records atomically
4. Returns appropriate HTTP status codes

### Payment Verification

**GET** `/api/payments/verify/{reference}/`

Manually verify a payment status by calling Paystack's verify endpoint.

**Response:**
```json
{
  "reference": "PAY_20240122123456_ABC12345",
  "status": "success",
  "amount": 100000,
  "currency": "NGN",
  "customer_email": "customer@example.com",
  "paid_at": "2024-01-22T12:35:30Z",
  "verification_data": {...}
}
```

## 🧪 Testing

### Run Tests

```powershell
# Run all tests
python manage.py test

# Run specific test modules
python manage.py test payments.tests.test_models
python manage.py test payments.tests.test_services
python manage.py test payments.tests.test_api

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

### Test Categories

- **Model Tests**: Payment and UserProfile model validation
- **Service Tests**: Paystack API integration and business logic
- **API Tests**: Endpoint behavior and response validation
- **Integration Tests**: End-to-end payment flow testing

## 🌐 Webhook Testing with ngrok

### Setup ngrok

1. **Install ngrok**: Download from [ngrok.com](https://ngrok.com/)
2. **Start tunnel**: `ngrok http 8000`
3. **Copy HTTPS URL**: e.g., `https://abc123.ngrok.io`
4. **Configure Paystack**: Add `https://abc123.ngrok.io/api/payments/webhook/` to your Paystack Dashboard

### Test Webhook

```powershell
# Create a test webhook payload
curl -X POST https://abc123.ngrok.io/api/payments/webhook/ \
  -H "Content-Type: application/json" \
  -H "x-paystack-signature: COMPUTED_SIGNATURE" \
  -d '{
    "event": "charge.success",
    "data": {
      "reference": "PAY_TEST_REF",
      "status": "success",
      "amount": 100000
    }
  }'
```

## 🔐 Security Considerations

### Environment Variables
- Never commit API keys to version control
- Use different keys for development/production
- Store secrets in environment variables or secret managers

### Webhook Security
- Always verify `x-paystack-signature` header
- Use constant-time comparison to prevent timing attacks
- Implement proper error handling without exposing internals

### Database Security
- Use `select_for_update()` for concurrent payment processing
- Implement proper transaction rollback on errors
- Add database constraints for data integrity

### API Security
- Validate all input parameters
- Implement rate limiting (when Redis is available)
- Use CORS headers appropriately
- Add comprehensive logging without exposing secrets

## 📊 Monitoring and Logging

### Log Levels

- **INFO**: Normal payment operations
- **WARNING**: Failed webhook signatures, payment failures
- **ERROR**: API errors, database issues
- **DEBUG**: Development debugging (disabled in production)

### Log Files

- **payments.log**: Application-specific logs
- **django.log**: Framework-level logs

### Structured Logging

```python
logger.info(f"Payment initialized: {reference} for {email}, amount: ₦{amount}")
logger.warning(f"Webhook signature verification failed for reference: {reference}")
logger.error(f"Paystack API error: {error_message}")
```

## 🚀 Production Deployment

### Environment Setup

1. **Set DEBUG=False** in production
2. **Configure PostgreSQL** database
3. **Setup Redis** for caching and rate limiting
4. **Configure HTTPS** for webhook endpoints
5. **Set proper CORS** origins
6. **Enable logging** to files

### Deployment Checklist

- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Static files collected
- [ ] HTTPS enabled for webhooks
- [ ] Paystack webhook URL configured
- [ ] Monitoring and alerts setup
- [ ] Backup strategy implemented

### Docker Setup (Optional)

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "payment_project.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section below
- Review the API documentation

## 🔧 Troubleshooting

### Common Issues

**1. Webhook signature verification fails**
- Ensure the secret key matches your Paystack dashboard
- Check that the raw request body is used for signature computation
- Verify HTTPS is used for webhook endpoints

**2. Database connection errors**
- Check PostgreSQL service is running
- Verify connection credentials in `.env` file
- Ensure database exists and migrations are applied

**3. Payment not updating after webhook**
- Check webhook signature is valid
- Verify payment reference exists in database
- Review application logs for error details

**4. Rate limiting issues**
- Ensure Redis is running and accessible
- Check Redis connection settings
- Consider disabling rate limiting in development

### Debug Mode

Enable debug logging by setting `DEBUG=True` and checking logs:

```powershell
tail -f payments.log
```

## 📈 Performance Considerations

- Use database connection pooling in production
- Implement caching for frequently accessed data
- Monitor webhook processing times
- Set up database indexing for large datasets
- Consider async processing for high-volume webhooks

## 🔄 API Versioning

The API uses URL-based versioning. Current version is v1 (implicit).
Future versions will use `/api/v2/payments/` pattern.

---

**Built with ❤️ using Django REST Framework and Paystack**