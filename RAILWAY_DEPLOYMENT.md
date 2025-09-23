# 🚀 Railway Deployment Guide for Django Paystack Integration

This guide will help you deploy your Django Paystack payment system to Railway, enabling **live webhooks** that automatically update payment status.

## **📋 Pre-Deployment Checklist**

✅ All deployment files created:
- `requirements.txt` (with gunicorn, whitenoise, etc.)
- `runtime.txt` (Python version)
- `Procfile` (web and release commands)
- `railway.json` (Railway configuration)

✅ Settings configured for production:
- WhiteNoise for static files
- Railway-compatible ALLOWED_HOSTS
- PostgreSQL database configuration

## **🚀 Deployment Steps**

### **Step 1: Create Railway Account**
1. Go to https://railway.app
2. Sign up with GitHub (recommended)
3. Verify your email

### **Step 2: Deploy from GitHub**

#### Option A: GitHub Integration (Recommended)
1. Push your code to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Django Paystack Payment System"
   git remote add origin https://github.com/yourusername/payment-app.git
   git push -u origin main
   ```

2. In Railway Dashboard:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will auto-detect Django and start building

#### Option B: Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up
```

### **Step 3: Add PostgreSQL Database**
1. In Railway Dashboard, click your project
2. Click "New Service" → "Database" → "PostgreSQL"
3. Railway automatically creates database and connection variables

### **Step 4: Configure Environment Variables**
In Railway Dashboard → Variables, add:

```env
# Django Configuration
SECRET_KEY=your-super-secret-key-here-make-it-random
DEBUG=False
ALLOWED_HOSTS=*.railway.app,*.up.railway.app

# Database (Auto-configured by Railway PostgreSQL)
# DATABASE_URL is automatically set by Railway

# Paystack Configuration
PAYSTACK_SECRET_KEY=sk_test_your_secret_key_here
PAYSTACK_PUBLIC_KEY=pk_test_your_public_key_here
PAYSTACK_BASE_URL=https://api.paystack.co

# Superuser Auto-Creation (IMPORTANT!)
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@gmail.com
ADMIN_PASSWORD=Paystack123

# Application URLs
FRONTEND_CALLBACK_URL=https://your-app.railway.app/payment/callback
BACKEND_WEBHOOK_URL=https://your-app.railway.app/api/payments/webhook/
```

**🔑 Important**: Replace `your-app.railway.app` with your actual Railway URL!

### **Step 5: Automatic Superuser Creation**

🎉 **Great News!** Your superuser is created automatically during deployment!

The deployment process runs:
```bash
python manage.py create_superuser_if_none_exists
```

This creates an admin user with the credentials from your environment variables:
- **Username**: `admin`
- **Email**: `admin@gmail.com`  
- **Password**: `Paystack123`

**Check the deployment logs** to confirm:
```
✅ Superuser created successfully!
   Username: admin
   Email: admin@gmail.com
   You can now log in to /admin/ with these credentials.
```

**Manual Creation (if needed):**
```bash
# Using Railway CLI (if auto-creation fails)
railway run python manage.py create_superuser_if_none_exists --force
```

## **🎯 Configure Paystack Webhooks**

### **Step 6: Get Your Railway URL**
1. In Railway Dashboard, find your app URL (e.g., `https://payment-app-production-abc123.up.railway.app`)
2. Your webhook URL will be: `https://your-url.railway.app/api/payments/webhook/`

### **Step 7: Update Paystack Dashboard**
1. Go to https://dashboard.paystack.com/settings/developer
2. Under "Webhooks", set URL to: `https://your-url.railway.app/api/payments/webhook/`
3. Save settings

## **🧪 Testing the Live System**

### **Test 1: Homepage Access**
- Visit: `https://your-url.railway.app/`
- Should see the beautiful payment interface
- Admin panel: `https://your-url.railway.app/admin/`
- API docs: `https://your-url.railway.app/api/docs/`

### **Test 2: Payment Flow**
1. Go to your Railway homepage
2. Enter email and amount
3. Click "Initialize Payment" - should redirect to Paystack
4. Use Paystack test cards:
   - **Success**: `4084084084084081` (CVV: 408, any future date)
   - **Failed**: `4084084084084081` (CVV: 000)

### **Test 3: Webhook Verification**
After completing payment on Paystack:

**Expected Results:**
- ✅ Payment status changes from "Pending" to "Success" 
- ✅ "Webhook verified" shows as True in admin panel
- ✅ User profile payment status becomes "Completed"
- ✅ Frontend refresh button shows updated data

**Check Railway Logs:**
```bash
railway logs
```
Should see:
```
✅ Payment processed successfully: PAY_xxx
Updated user profile for user@example.com to completed
```

## **🔧 Troubleshooting**

### **Deployment Issues**
- **Build fails**: Check `requirements.txt` syntax
- **Static files missing**: Ensure WhiteNoise is configured
- **Database errors**: Verify PostgreSQL service is added

### **Webhook Issues**
- **Status stays pending**: Check Railway URL in Paystack dashboard
- **403 errors**: Verify PAYSTACK_SECRET_KEY is correct
- **500 errors**: Check Railway logs for detailed error messages

### **Debug Commands**
```bash
# View logs
railway logs --follow

# Run Django commands
railway run python manage.py shell
railway run python manage.py migrate

# Check environment variables
railway variables
```

## **🎯 Production Checklist**

Before going live:
- [ ] Use strong SECRET_KEY (generate new one)
- [ ] Set DEBUG=False
- [ ] Configure proper domain in ALLOWED_HOSTS
- [ ] Use production Paystack keys (sk_live_... and pk_live_...)
- [ ] Set up SSL certificate (Railway provides this automatically)
- [ ] Configure monitoring and error tracking

## **🚀 Benefits of Railway Deployment**

✅ **Live HTTPS URLs** - Paystack webhooks work immediately
✅ **Automatic PostgreSQL** - Production-ready database
✅ **Easy scaling** - Handle more traffic as needed
✅ **Automatic SSL** - Secure webhook endpoints
✅ **GitHub integration** - Deploy on every push
✅ **Environment management** - Secure secret handling

## **💡 Next Steps**

1. **Custom Domain**: Configure your own domain name
2. **Monitoring**: Set up error tracking (Sentry)
3. **CI/CD**: Automatic testing before deployment
4. **Redis**: Add Redis for caching and rate limiting
5. **Backup**: Configure database backups

---

**🎉 Congratulations!** Your Django Paystack Payment System is now live with fully functional webhooks!