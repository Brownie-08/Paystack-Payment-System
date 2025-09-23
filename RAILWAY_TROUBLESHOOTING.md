# 🔧 Railway Deployment Troubleshooting Guide

## If you're still getting build errors, try these solutions:

### **Option 1: Force Railway to Detect Python App**

1. **In Railway Dashboard:**
   - Go to your project settings
   - Under "Build", click "Configure"
   - Set "Build Command": `pip install -r requirements.txt`
   - Set "Start Command": `gunicorn payment_project.wsgi:application --bind 0.0.0.0:$PORT`

### **Option 2: Use Railway CLI (Most Reliable)**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Deploy directly
railway up
```

### **Option 3: Manual Service Configuration**

In Railway Dashboard:
1. **Variables Tab** - Add all environment variables
2. **Settings Tab** - Set:
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate && python manage.py create_superuser_if_none_exists`
   - **Start Command**: `gunicorn payment_project.wsgi:application --bind 0.0.0.0:$PORT`
   - **Root Directory**: (leave empty)

### **Option 4: Alternative Requirements (if psycopg2 still fails)**

Replace in `requirements.txt`:
```txt
# Instead of psycopg2-binary, use:
django-environ==0.11.2
dj-database-url==2.1.0

# And add to settings.py:
# Use SQLite for initial deployment, then switch to PostgreSQL
```

### **Environment Variables (Copy-Paste Ready)**

```bash
SECRET_KEY=^f+t(2fic6j412bzl0e*fjj%vla8v!koevj-b!oo&1imk1xh1c
DEBUG=False
ALLOWED_HOSTS=*.railway.app,*.up.railway.app
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@gmail.com
ADMIN_PASSWORD=Paystack123
PAYSTACK_SECRET_KEY=sk_test_your_actual_key_here
PAYSTACK_PUBLIC_KEY=pk_test_your_actual_key_here
PAYSTACK_BASE_URL=https://api.paystack.co
CORS_ALLOW_ALL_ORIGINS=True
```

### **Quick Fix: Use Simple Start Command**

If all else fails, try this in Railway Settings:
- **Start Command**: `python manage.py runserver 0.0.0.0:$PORT`
- This uses Django's built-in server (not recommended for production traffic, but works for testing)

### **Debug Railway Build Issues**

1. **Check Railway Logs** - Look for specific error messages
2. **Try Different Python Version** - Change `runtime.txt` to `python-3.10.12`
3. **Remove nixpacks.toml** - Let Railway auto-detect
4. **Contact Railway Support** - They're very responsive on Discord

### **Success Indicators**

Look for these in Railway logs:
```
✅ Installing Python dependencies
✅ Collecting static files
✅ Running migrations
✅ Superuser created successfully!
   Username: admin
   Email: admin@gmail.com
✅ Starting gunicorn
```

### **Alternative: Use Heroku or Render**

If Railway continues to have issues:
- **Heroku**: Similar process, very reliable
- **Render**: Even simpler, auto-detects Django
- **DigitalOcean App Platform**: Good Railway alternative

Let me know which approach works best for you!