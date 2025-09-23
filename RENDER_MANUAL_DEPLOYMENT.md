# Manual Render Deployment Guide

If the Blueprint (render.yaml) approach doesn't work, here's how to deploy manually to Render.

## Step-by-Step Manual Deployment

### Step 1: Create PostgreSQL Database

1. **Go to Render Dashboard**: https://render.com/dashboard
2. **Create Database**:
   - Click "New +" → "PostgreSQL"
   - Name: `paystack-payment-db`
   - Database Name: `paystack_payment`
   - User: `paystack_user`
   - Region: `Oregon (US West)`
   - Plan: `Free`
   - Click "Create Database"

3. **Note Database Details**:
   - After creation, go to the database dashboard
   - Copy the "Internal Database URL" (starts with `postgresql://`)
   - Keep this handy for the web service setup

### Step 2: Create Web Service

1. **Create Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub account if not already connected
   - Select your repository: `Paystack-Payment-System`
   - Click "Connect"

2. **Configure Web Service**:
   ```
   Name: paystack-payment-app
   Region: Oregon (US West)
   Branch: main
   Root Directory: (leave blank)
   Runtime: Python 3
   Build Command: ./build.sh
   Start Command: gunicorn payment_project.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120
   Instance Type: Free
   ```

### Step 3: Set Environment Variables

In the web service dashboard, go to "Environment" tab and add these variables:

#### Required Variables:
```
DEBUG=false
SECRET_KEY=[Click "Generate" to auto-generate]
DATABASE_URL=[Paste the Internal Database URL from Step 1]
```

#### Paystack Configuration:
```
PAYSTACK_SECRET_KEY=sk_test_your_actual_secret_key
PAYSTACK_PUBLIC_KEY=pk_test_your_actual_public_key
PAYSTACK_BASE_URL=https://api.paystack.co
```

#### URL Configuration:
```
FRONTEND_CALLBACK_URL=https://yourfrontend.com/payment/callback
BACKEND_WEBHOOK_URL=https://paystack-payment-app.onrender.com/api/payments/webhook/
RENDER_EXTERNAL_URL=https://paystack-payment-app.onrender.com
RENDER_EXTERNAL_HOSTNAME=paystack-payment-app.onrender.com
```

#### CORS Configuration:
```
CORS_ALLOW_ALL_ORIGINS=false
```

### Step 4: Deploy

1. **Click "Create Web Service"**
2. **Wait for Build**: The first build will take 5-10 minutes
3. **Monitor Logs**: Check the "Logs" tab for any issues

### Step 5: Verify Deployment

1. **Check Service URL**: Your app will be available at `https://paystack-payment-app.onrender.com`
2. **Test Health Endpoint**: 
   ```
   curl https://paystack-payment-app.onrender.com/api/payments/health/
   ```
3. **Test API Documentation**:
   ```
   https://paystack-payment-app.onrender.com/api/schema/swagger-ui/
   ```

### Step 6: Update Paystack Webhook

1. **Go to Paystack Dashboard**: https://dashboard.paystack.com
2. **Navigate to**: Settings → Webhooks
3. **Update Webhook URL**: `https://paystack-payment-app.onrender.com/api/payments/webhook/`

## Troubleshooting Manual Deployment

### Build Issues

**Issue**: Build fails with "permission denied: ./build.sh"
**Solution**: 
```bash
# In your local repo
git update-index --chmod=+x build.sh
git commit -m "Make build.sh executable"
git push origin main
```

**Issue**: Python version issues
**Solution**: Add `PYTHON_VERSION=3.11.0` to environment variables

### Database Issues

**Issue**: Database connection failed
**Solution**:
1. Verify `DATABASE_URL` is correctly set
2. Ensure database and web service are in the same region
3. Check database status in Render dashboard

**Issue**: Migration failures
**Solution**: 
1. Check if `build.sh` includes `python manage.py migrate`
2. Verify PostgreSQL dependencies in `requirements.txt`

### Environment Variable Issues

**Issue**: Paystack API calls failing
**Solution**:
1. Verify `PAYSTACK_SECRET_KEY` and `PAYSTACK_PUBLIC_KEY` are set correctly
2. Ensure no extra spaces in the keys
3. Test keys in Paystack dashboard first

### SSL/HTTPS Issues

**Issue**: Mixed content errors
**Solution**:
1. Ensure all URLs in environment variables use `https://`
2. Update CORS and CSRF settings for HTTPS

## Monitoring and Maintenance

### Check Service Health
```bash
# Quick health check
curl https://paystack-payment-app.onrender.com/api/payments/health/

# Check database connection
curl https://paystack-payment-app.onrender.com/api/payments/health/db/
```

### View Logs
1. Go to Render Dashboard
2. Select your web service
3. Click "Logs" tab
4. Monitor for errors or performance issues

### Update Environment Variables
1. Go to web service dashboard
2. Click "Environment" tab
3. Update variables as needed
4. Service will automatically restart

## Alternative: Use Render CLI

If you prefer command-line deployment:

1. **Install Render CLI**:
   ```bash
   npm install -g @render/cli
   ```

2. **Login**:
   ```bash
   render login
   ```

3. **Deploy**:
   ```bash
   render deploy
   ```

## Production Checklist

- [ ] Database created and connected
- [ ] Web service deployed successfully
- [ ] All environment variables set
- [ ] Paystack webhook URL updated
- [ ] SSL certificate active (automatic)
- [ ] API endpoints responding
- [ ] Payment flow tested with test cards
- [ ] Error monitoring set up
- [ ] Backup strategy in place

## Support Resources

- **Render Docs**: https://render.com/docs
- **Django Deployment**: https://render.com/docs/deploy-django
- **PostgreSQL on Render**: https://render.com/docs/databases
- **Environment Variables**: https://render.com/docs/environment-variables

---

**Note**: Manual deployment gives you more control but requires more steps. The Blueprint approach is easier when it works correctly.