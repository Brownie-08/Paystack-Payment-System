# Admin Dashboard Setup Guide for Render Deployment

This guide will help you set up admin access for your Django Paystack Payment App deployed on Render.

## 🚨 Admin Access Issue - Quick Fix

If you can't access the admin dashboard on your deployed app, follow these steps:

### Method 1: Set Environment Variables in Render (Recommended)

1. **Go to your Render Dashboard**:
   - Navigate to https://render.com/dashboard
   - Find your web service for this app
   - Click on your service name

2. **Add Admin Environment Variables**:
   - Go to the "Environment" tab
   - Click "Add Environment Variable"
   - Add these variables:

   ```
   ADMIN_USERNAME=youradmin
   ADMIN_EMAIL=admin@yourdomain.com
   ADMIN_PASSWORD=YourSecurePassword123!
   
   # Alternative Django method (optional)
   DJANGO_SUPERUSER_USERNAME=youradmin
   DJANGO_SUPERUSER_EMAIL=admin@yourdomain.com
   DJANGO_SUPERUSER_PASSWORD=YourSecurePassword123!
   ```

3. **Redeploy Your App**:
   - After adding the variables, click "Save Changes"
   - This will trigger a new deployment
   - The build.sh script will automatically create the admin user

4. **Access Admin Panel**:
   - Once deployment completes, visit: `https://your-app-name.onrender.com/admin/`
   - Login with your configured credentials

### Method 2: Manual Admin Creation (If Environment Variables Don't Work)

1. **Connect to Render Shell** (if available on your plan):
   ```bash
   # This may not be available on free tier
   render shell --service your-service-name
   ```

2. **Create Admin User Manually**:
   ```bash
   python manage.py create_admin
   # or
   python manage.py create_superuser_if_none_exists
   ```

### Method 3: Update and Redeploy (Guaranteed Fix)

1. **Clone/Update Your Repository**:
   ```bash
   git clone your-repo-url
   cd Payment_App
   ```

2. **Update build.sh** (already done in this fix):
   - The build.sh now includes multiple admin creation methods
   - It will try all available methods during deployment

3. **Set Environment Variables**:
   - In your Render dashboard, add the admin environment variables listed above

4. **Push and Deploy**:
   ```bash
   git add .
   git commit -m "Fix admin user creation for Render deployment"
   git push origin main
   ```

## 🔐 Security Best Practices

### For Production:
- **Use Strong Passwords**: At least 12 characters with mixed case, numbers, and symbols
- **Use Real Email**: Use a real email address you control
- **Unique Username**: Don't use "admin" - use something unique
- **Regular Updates**: Change admin password regularly

### Environment Variable Examples:
```bash
# Production Example
ADMIN_USERNAME=mycompany_admin
ADMIN_EMAIL=admin@mycompany.com
ADMIN_PASSWORD=MyComplex$Password123!

# Development Example
ADMIN_USERNAME=dev_admin
ADMIN_EMAIL=dev@localhost.com
ADMIN_PASSWORD=DevPassword123
```

## 🧪 Testing Admin Access

### 1. Check if Admin User Exists

You can test locally or check logs during deployment:

```bash
# Check if any superusers exist
python manage.py shell -c "from django.contrib.auth.models import User; print('Superusers:', list(User.objects.filter(is_superuser=True).values_list('username', 'email')))"
```

### 2. Create Admin User Locally (for testing):

```bash
# Method 1: Using our custom command
python manage.py create_admin

# Method 2: Using the comprehensive command
python manage.py create_superuser_if_none_exists

# Method 3: Django's built-in (interactive)
python manage.py createsuperuser
```

### 3. Test Admin Login:

1. Start local server: `python manage.py runserver`
2. Visit: http://127.0.0.1:8000/admin/
3. Login with your admin credentials
4. Verify you can see the Payment and UserProfile models

## 🔍 Troubleshooting

### Problem: "Admin user already exists" but can't login

**Solution**: The username exists but password might be wrong.

```bash
# Reset admin password
python manage.py shell -c "
from django.contrib.auth.models import User
user = User.objects.get(username='admin')  # replace 'admin' with your username
user.set_password('YourNewPassword123!')
user.save()
print('Password updated successfully')
"
```

### Problem: Environment variables not working

**Possible causes**:
1. **Typos in variable names**: Check spelling exactly
2. **Spaces in values**: Make sure no trailing spaces
3. **Render caching**: Try manual deploy after setting variables

**Solution**:
1. Double-check variable names in Render dashboard
2. Clear any trailing spaces
3. Use "Manual Deploy" button in Render

### Problem: Build fails during admin creation

**Check build logs** in Render dashboard for:
- Database connection errors
- Python import errors
- Permission issues

**Common fixes**:
1. Ensure DATABASE_URL is set correctly
2. Verify all migrations ran successfully
3. Check that app starts without admin creation first

## 📝 What the Build Script Does

The updated `build.sh` now:

1. **Runs migrations**: Ensures database is ready
2. **Tries multiple admin creation methods**:
   - Django's built-in `createsuperuser --noinput`
   - Our custom `create_admin` command
   - Our comprehensive `create_superuser_if_none_exists` command
3. **Shows final status**: Lists existing superusers
4. **Handles failures gracefully**: Won't stop deployment if admin creation fails

## 🚀 Environment Variables for Render

Add these in your Render dashboard under Environment tab:

```bash
# Required - Basic Django
DEBUG=false
SECRET_KEY=[Auto-generated by Render]
DATABASE_URL=[Auto-set by Render PostgreSQL]

# Required - Paystack
PAYSTACK_SECRET_KEY=sk_live_your_live_key  # or sk_test_ for testing
PAYSTACK_PUBLIC_KEY=pk_live_your_live_key  # or pk_test_ for testing

# Required - Admin Access (CHOOSE SECURE VALUES!)
ADMIN_USERNAME=your_secure_username
ADMIN_EMAIL=your_real_email@domain.com
ADMIN_PASSWORD=YourVerySecurePassword123!

# Optional - Alternative admin method
DJANGO_SUPERUSER_USERNAME=your_secure_username
DJANGO_SUPERUSER_EMAIL=your_real_email@domain.com  
DJANGO_SUPERUSER_PASSWORD=YourVerySecurePassword123!

# Optional - URLs
RENDER_EXTERNAL_URL=https://your-app-name.onrender.com
BACKEND_WEBHOOK_URL=https://your-app-name.onrender.com/api/payments/webhook/
```

## ✅ Verification Steps

After deployment:

1. **Check deployment logs** for admin creation messages
2. **Visit admin URL**: `https://your-app-name.onrender.com/admin/`
3. **Login with your credentials**
4. **Verify you can see**:
   - Payment records
   - User management
   - Django admin interface

## 🆘 Still Having Issues?

If you're still unable to access the admin dashboard:

1. **Check Render logs** during deployment
2. **Verify all environment variables** are set correctly
3. **Try a manual deployment** after adding variables
4. **Contact support** with specific error messages from logs

---

**Last Updated**: January 2024  
**Compatibility**: Django 4.2+, Render Free/Paid Tiers