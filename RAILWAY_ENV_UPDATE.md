# 🚀 Railway Environment Variables Update

Based on your app URL: `https://paystack-payment-system-production.up.railway.app`

## ✅ **Add These Environment Variables to Railway:**

Go to Railway Dashboard → Your Project → Variables → Add these:

```bash
# Django Security
SECRET_KEY=^f+t(2fic6j412bzl0e*fjj%vla8v!koevj-b!oo&1imk1xh1c
DEBUG=False
RAILWAY_ENVIRONMENT=production

# Specific Railway Domain Configuration
RAILWAY_STATIC_URL=https://paystack-payment-system-production.up.railway.app
CSRF_TRUSTED_ORIGINS=https://paystack-payment-system-production.up.railway.app
ALLOWED_HOSTS=paystack-payment-system-production.up.railway.app,*.railway.app,*.up.railway.app

# Superuser Auto-Creation
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@gmail.com
ADMIN_PASSWORD=Paystack123

# Paystack Configuration
PAYSTACK_SECRET_KEY=sk_test_your_actual_key_here
PAYSTACK_PUBLIC_KEY=pk_test_your_actual_key_here
PAYSTACK_BASE_URL=https://api.paystack.co

# CORS Settings
CORS_ALLOW_ALL_ORIGINS=True

# Webhook URL (for your Paystack dashboard)
BACKEND_WEBHOOK_URL=https://paystack-payment-system-production.up.railway.app/api/payments/webhook/
```

## 🔧 **Paystack Dashboard Webhook Setup:**

1. **Go to**: https://dashboard.paystack.com/settings/developer
2. **Webhook URL**: `https://paystack-payment-system-production.up.railway.app/api/payments/webhook/`
3. **Events to Subscribe**: 
   - ✅ `charge.success`
   - ✅ `charge.failed` (optional)

## 🎯 **After Adding These Variables:**

1. **Railway will auto-redeploy**
2. **Admin login should work**: `/admin/`
3. **Webhooks should work**: Payments will update from "Pending" to "Success"
4. **CSRF errors should be gone**

## 🚀 **Test After Deployment:**

1. **Admin Login**: `https://paystack-payment-system-production.up.railway.app/admin/`
2. **Make Test Payment**: Use the payment form
3. **Check Webhook**: Payment should change from "Pending" to "Success"
4. **Verify in Admin**: Check that payment shows "Webhook Verified: True"

This should fix both the CSRF 403 error and the webhook pending status! 🎉