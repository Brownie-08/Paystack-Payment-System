# 🚀 ngrok Setup for Paystack Webhook Testing

## **Install ngrok**

### **Option 1: Download from Website**
1. Go to https://ngrok.com/download
2. Download the Windows version
3. Extract `ngrok.exe` to a folder (e.g., `C:\ngrok\`)
4. Add the folder to your PATH environment variable

### **Option 2: Using Chocolatey**
```powershell
# Run PowerShell as Administrator
choco install ngrok
```

### **Option 3: Using Scoop**
```powershell
scoop install ngrok
```

## **Setup Steps**

### **1. Create ngrok Account** (Optional but recommended)
1. Go to https://dashboard.ngrok.com/signup
2. Sign up for a free account
3. Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken

### **2. Configure ngrok** (If you have an account)
```bash
ngrok config add-authtoken YOUR_AUTHTOKEN_HERE
```

### **3. Start Django Server**
```bash
# In your Payment_App directory
python manage.py runserver 127.0.0.1:8000
```

### **4. Start ngrok Tunnel**
Open a new terminal/PowerShell and run:
```bash
# Forward port 8000 to public ngrok URL
ngrok http 8000
```

You'll see output like:
```
Session Status      online
Account             Your Account (Plan: Free)
Version             3.1.0
Region              United States (us)
Web Interface       http://127.0.0.1:4040
Forwarding          https://abc123def.ngrok.io -> http://localhost:8000
```

### **5. Update Paystack Webhook URL**

1. Copy the `https://abc123def.ngrok.io` URL from ngrok
2. Go to https://dashboard.paystack.com/settings/developer
3. Set webhook URL to: `https://abc123def.ngrok.io/api/payments/webhook/`
4. Save the settings

## **Test the Webhook**

### **Method 1: Use our Test Script**
```bash
python test_webhook.py https://abc123def.ngrok.io
```

### **Method 2: Real Payment Test**
1. Go to your homepage: http://127.0.0.1:8000/
2. Create a payment
3. Use Paystack test cards:
   - **Success**: `4084084084084081` (any CVV, future date)
   - **Insufficient Funds**: `4084084084084081` with CVV `000`
   - **Declined**: `4084084084084081` with CVV `111`

### **Method 3: Paystack Dashboard Test**
1. Go to https://dashboard.paystack.com/settings/developer
2. Click "Test Webhook" button
3. Check Django logs and admin panel

## **Verification**

After successful webhook:
- ✅ Django logs show "✅ Payment processed successfully"
- ✅ Admin panel shows payment status as "Success"
- ✅ Admin panel shows "Webhook verified = True"
- ✅ User profile shows "Payment status = completed"

## **Troubleshooting**

### **ngrok not found**
- Make sure ngrok is in your PATH
- Or run with full path: `C:\path\to\ngrok.exe http 8000`

### **Webhook not triggering**
- Check ngrok is running and forwarding port 8000
- Verify webhook URL in Paystack dashboard
- Check Django server is running on 127.0.0.1:8000
- Look at ngrok web interface: http://127.0.0.1:4040

### **Signature verification fails**
- Ensure you're using the correct PAYSTACK_SECRET_KEY
- Check the key in your `.env` file matches Paystack dashboard

### **Payment not updating**
- Check Django logs for errors
- Verify transaction verification with Paystack API
- Check database connection is working
- Ensure webhook_received and webhook_verified fields update

## **Production Setup**

For production, replace ngrok with:
- **Heroku**: Automatic HTTPS URLs
- **AWS/DigitalOcean**: Configure HTTPS with Let's Encrypt
- **Cloudflare**: HTTPS proxy with tunnel

Set webhook URL to: `https://yourdomain.com/api/payments/webhook/`