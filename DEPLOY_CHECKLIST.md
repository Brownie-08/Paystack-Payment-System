# ✅ Railway Deployment Checklist

## **📋 Pre-Deployment (COMPLETED)**

✅ **Deployment Files Created**:
- `requirements.txt` - All dependencies including gunicorn, whitenoise
- `runtime.txt` - Python 3.11.7
- `Procfile` - Web server and migration commands
- `railway.json` - Railway configuration

✅ **Django Settings Configured**:
- WhiteNoise middleware for static files
- Railway ALLOWED_HOSTS (`*.railway.app`, `*.up.railway.app`)
- DATABASE_URL support with dj-database-url
- Production-ready logging

✅ **Code Quality**:
- Webhook system with HMAC SHA512 verification
- PostgreSQL database integration
- Error handling and logging
- Beautiful frontend interface

## **🚀 Deploy to Railway**

### **Step 1: Create Railway Account**
1. Go to https://railway.app
2. Sign up with GitHub
3. Verify email

### **Step 2: Deploy**
1. **Option A - GitHub**: Push code to GitHub, deploy from Railway dashboard
2. **Option B - Direct**: Use Railway CLI to deploy directly

### **Step 3: Add Database**
1. In Railway project dashboard
2. "New Service" → "Database" → "PostgreSQL" 
3. Railway auto-configures DATABASE_URL

### **Step 4: Environment Variables**
Add in Railway Variables:

```
SECRET_KEY=generate-random-secret-key-here
DEBUG=False
PAYSTACK_SECRET_KEY=sk_test_your_secret_key_here
PAYSTACK_PUBLIC_KEY=pk_test_your_public_key_here
```

### **Step 5: Create Superuser**
```bash
railway run python manage.py createsuperuser
```

## **🎯 Configure Paystack Webhook**

### **Get Railway URL**
Your app will be at: `https://payment-app-production-xxxxx.up.railway.app`

### **Update Paystack Dashboard**
1. Go to https://dashboard.paystack.com/settings/developer
2. Set Webhook URL: `https://your-railway-url.up.railway.app/api/payments/webhook/`
3. Save settings

## **🧪 Test Everything**

### **Test 1: Website Access**
- Visit your Railway URL
- Should see payment interface
- Admin: `/admin/`
- API docs: `/api/docs/`

### **Test 2: Payment Flow**
1. Initialize payment from homepage
2. Complete on Paystack with test card: `4084084084084081`
3. **Check webhook works**:
   - Payment status: Pending → Success
   - Webhook verified: True
   - User profile: Completed

### **Test 3: Verify Logs**
```bash
railway logs
```
Should show:
```
✅ Payment processed successfully: PAY_xxx
Updated user profile for user@email.com to completed
```

## **🎉 SUCCESS CRITERIA**

✅ **Railway deployment successful**  
✅ **Database connected (PostgreSQL)**  
✅ **Homepage loads correctly**  
✅ **Payment initialization works**  
✅ **Paystack redirect functions**  
✅ **Webhook receives and processes events**  
✅ **Database updates automatically**  
✅ **Admin panel accessible**  

## **💡 Troubleshooting**

**Build Fails**: Check requirements.txt syntax  
**Database Issues**: Verify PostgreSQL service added  
**Webhook 403**: Check PAYSTACK_SECRET_KEY matches dashboard  
**Status Not Updating**: Verify webhook URL in Paystack dashboard  

## **🔥 Go Live!**

Your Django Paystack Payment System is now **LIVE** with fully functional webhooks!

**Next Steps:**
1. Test with real payments
2. Monitor Railway logs
3. Set up custom domain (optional)
4. Switch to production Paystack keys when ready