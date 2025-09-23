# Payment API Documentation

This document provides comprehensive API documentation for the Django Paystack Payment Integration system.

## Base URL
```
http://localhost:8000/api/payments/
```

## Authentication
Currently, the API allows anonymous access for all endpoints. In production, you should implement proper authentication.

## Content Type
All requests should use `application/json` content type.

---

## Endpoints

### 1. Initialize Payment

Initialize a new payment transaction with Paystack.

**Endpoint:** `POST /api/payments/initiate/`

#### Request Body
```json
{
  "email": "customer@example.com",
  "amount": "1000.00",
  "callback_url": "https://yourapp.com/callback" // optional
}
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| email | string | Yes | Customer's email address |
| amount | string | Yes | Amount in Naira (min: 1.00, max: 1,000,000.00) |
| callback_url | string | No | Optional callback URL for redirect after payment |

#### Response
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

#### Status Codes
- `201 Created` - Payment initialized successfully
- `400 Bad Request` - Invalid request data
- `500 Internal Server Error` - Payment initialization failed

#### Example Request
```bash
curl -X POST http://localhost:8000/api/payments/initiate/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "amount": "1000.00",
    "callback_url": "https://yourapp.com/callback"
  }'
```

---

### 2. Webhook Handler

Handle webhook notifications from Paystack.

**Endpoint:** `POST /api/payments/webhook/`

#### Headers
| Header | Required | Description |
|--------|----------|-------------|
| x-paystack-signature | Yes | HMAC SHA512 signature of the payload |
| Content-Type | Yes | application/json |

#### Webhook Payload (from Paystack)
```json
{
  "event": "charge.success",
  "data": {
    "reference": "PAY_20240122123456_ABC12345",
    "status": "success",
    "amount": 100000,
    "currency": "NGN",
    "paid_at": "2024-01-22T12:35:30Z",
    "customer": {
      "email": "customer@example.com"
    }
  }
}
```

#### Supported Events
- `charge.success` - Payment completed successfully
- Other events are ignored but return 200 OK

#### Response
- `200 OK` - Webhook processed successfully
- `403 Forbidden` - Invalid signature or missing signature header
- `400 Bad Request` - Invalid JSON payload
- `500 Internal Server Error` - Processing failed (Paystack will retry)

#### Signature Verification
The webhook signature is computed using HMAC SHA512:
```python
import hashlib
import hmac

signature = hmac.new(
    PAYSTACK_SECRET_KEY.encode('utf-8'),
    payload,
    hashlib.sha512
).hexdigest()
```

---

### 3. Verify Payment

Manually verify a payment status by calling Paystack's verify endpoint.

**Endpoint:** `GET /api/payments/verify/{reference}/`

#### URL Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| reference | string | Yes | Payment reference to verify |

#### Response
```json
{
  "reference": "PAY_20240122123456_ABC12345",
  "status": "success",
  "amount": 100000,
  "currency": "NGN",
  "customer_email": "customer@example.com",
  "paid_at": "2024-01-22T12:35:30Z",
  "verification_data": {
    "status": "success",
    "reference": "PAY_20240122123456_ABC12345",
    "amount": 100000,
    "gateway_response": "Successful",
    "paid_at": "2024-01-22T12:35:30Z",
    "created_at": "2024-01-22T12:34:56Z",
    "channel": "card",
    "currency": "NGN",
    "ip_address": "127.0.0.1"
  }
}
```

#### Status Codes
- `200 OK` - Verification successful
- `404 Not Found` - Payment reference not found
- `500 Internal Server Error` - Verification failed

#### Example Request
```bash
curl -X GET http://localhost:8000/api/payments/verify/PAY_20240122123456_ABC12345/
```

---

### 4. Payment Callback

Handle payment completion callback redirects from Paystack (optional UI flow).

**Endpoint:** `GET /api/payments/callback/`

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| reference | string | Yes | Payment reference |
| trxref | string | No | Transaction reference (optional) |

#### Response
```json
{
  "reference": "PAY_20240122123456_ABC12345",
  "status": "success",
  "amount": "1000.00",
  "customer_email": "customer@example.com",
  "message": "Callback received successfully"
}
```

#### Status Codes
- `200 OK` - Callback processed successfully
- `400 Bad Request` - Missing reference parameter
- `404 Not Found` - Payment not found

#### Example Request
```bash
curl -X GET "http://localhost:8000/api/payments/callback/?reference=PAY_20240122123456_ABC12345"
```

---

### 5. List Payments

Get a list of all payments with optional filtering.

**Endpoint:** `GET /api/payments/`

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| status | string | No | Filter by payment status |
| email | string | No | Filter by customer email (partial match) |

#### Payment Statuses
- `pending` - Payment initialized but not completed
- `processing` - Payment being processed by Paystack
- `success` - Payment completed successfully
- `failed` - Payment failed
- `cancelled` - Payment cancelled by user
- `abandoned` - Payment abandoned (timeout)

#### Response
```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "reference": "PAY_20240122123456_ABC12345",
    "customer_email": "customer@example.com",
    "amount": 100000,
    "amount_in_naira": 1000.00,
    "currency": "NGN",
    "status": "success",
    "status_display": "Success",
    "authorization_url": "https://checkout.paystack.com/xyz123",
    "webhook_received": true,
    "webhook_verified": true,
    "created_at": "2024-01-22T12:34:56Z",
    "updated_at": "2024-01-22T12:35:30Z",
    "paid_at": "2024-01-22T12:35:30Z"
  }
]
```

#### Example Requests
```bash
# Get all payments
curl -X GET http://localhost:8000/api/payments/

# Filter by status
curl -X GET "http://localhost:8000/api/payments/?status=success"

# Filter by email
curl -X GET "http://localhost:8000/api/payments/?email=customer@example.com"
```

---

### 6. Get Payment Details

Get detailed information about a specific payment.

**Endpoint:** `GET /api/payments/{reference}/`

#### URL Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| reference | string | Yes | Payment reference |

#### Response
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "reference": "PAY_20240122123456_ABC12345",
  "user_email": "user@example.com",
  "customer_email": "customer@example.com",
  "amount": 100000,
  "amount_in_naira": 1000.00,
  "currency": "NGN",
  "status": "success",
  "status_display": "Success",
  "authorization_url": "https://checkout.paystack.com/xyz123",
  "access_code": "xyz123abc",
  "webhook_received": true,
  "webhook_verified": true,
  "metadata": {
    "source": "web",
    "plan": "premium"
  },
  "created_at": "2024-01-22T12:34:56Z",
  "updated_at": "2024-01-22T12:35:30Z",
  "paid_at": "2024-01-22T12:35:30Z"
}
```

#### Status Codes
- `200 OK` - Payment found
- `404 Not Found` - Payment not found

#### Example Request
```bash
curl -X GET http://localhost:8000/api/payments/PAY_20240122123456_ABC12345/
```

---

## Error Responses

All error responses follow a consistent format:

```json
{
  "error": "Error description",
  "details": {
    "field_name": ["Specific error message"]
  },
  "timestamp": "2024-01-22T12:34:56Z"
}
```

### Common Error Codes

#### 400 Bad Request
```json
{
  "error": "Invalid request data",
  "details": {
    "email": ["Enter a valid email address."],
    "amount": ["Ensure this value is greater than or equal to 1.00."]
  },
  "timestamp": "2024-01-22T12:34:56Z"
}
```

#### 403 Forbidden (Webhook)
```json
{
  "error": "Invalid signature",
  "timestamp": "2024-01-22T12:34:56Z"
}
```

#### 404 Not Found
```json
{
  "error": "Payment not found",
  "details": {
    "reference": "PAY_INVALID_REF"
  },
  "timestamp": "2024-01-22T12:34:56Z"
}
```

#### 500 Internal Server Error
```json
{
  "error": "Payment initialization failed",
  "details": {
    "message": "Paystack API error: Invalid API key"
  },
  "timestamp": "2024-01-22T12:34:56Z"
}
```

---

## Integration Guide

### 1. Basic Payment Flow

1. **Initialize Payment**
   ```javascript
   const response = await fetch('/api/payments/initiate/', {
     method: 'POST',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({
       email: 'customer@example.com',
       amount: '1000.00'
     })
   });
   const payment = await response.json();
   ```

2. **Redirect to Paystack**
   ```javascript
   window.location.href = payment.authorization_url;
   ```

3. **Handle Webhook** (Server-side)
   - Verify signature
   - Update payment status
   - Update user account

### 2. Webhook Integration

#### Configure Paystack Dashboard
1. Go to Settings → Webhooks
2. Add webhook URL: `https://yourapp.com/api/payments/webhook/`
3. Select events: `charge.success`

#### Verify Webhook Signature
```python
import hashlib
import hmac

def verify_signature(payload, signature, secret_key):
    expected = hmac.new(
        secret_key.encode('utf-8'),
        payload,
        hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### 3. Testing with ngrok

1. Install ngrok: `npm install -g ngrok`
2. Start tunnel: `ngrok http 8000`
3. Update Paystack webhook URL: `https://abc123.ngrok.io/api/payments/webhook/`
4. Test payment flow

---

## Rate Limiting

When Redis is configured, the following rate limits apply:

- Payment initialization: 10 requests per minute per IP
- Payment verification: 20 requests per minute per IP
- Other endpoints: No rate limiting

---

## Security Considerations

1. **Always verify webhook signatures** before processing
2. **Use HTTPS** for webhook endpoints in production
3. **Validate all input** parameters
4. **Don't expose sensitive data** in error messages
5. **Monitor** for unusual payment patterns
6. **Implement proper logging** without exposing secrets

---

## Postman Collection

A Postman collection is available with all endpoints configured. Import the collection and set the following environment variables:

- `base_url`: http://localhost:8000
- `paystack_secret_key`: Your Paystack secret key (for signature generation)

---

## OpenAPI Specification

Interactive API documentation is available at:
- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI Schema: `/api/schema/`