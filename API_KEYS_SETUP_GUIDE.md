# API Keys Setup Guide for BUILD UP PILOT

## 📞 **Twilio Setup (For SMS OTP)**

### **1. Create Twilio Account**
- Go to: https://www.twilio.com/
- Click "Sign Up" → Free account
- Verify email and phone number
- Choose "SMS" service

### **2. Get Twilio Auth Token**
1. **Login to Twilio Console**: https://console.twilio.com/
2. **Go to Project Settings** (gear icon top right)
3. **Find "API Keys" section**
4. **Your Auth Token** will be displayed
5. **Copy the Auth Token** (starts with "AC" followed by numbers)

### **3. Get Twilio Phone Number**
1. **In Twilio Console**, go to "Phone Numbers" → "Manage"
2. **Click "Buy a Number"**
3. **Select "SMS" capability**
4. **Choose a number** (starts with +1 for US)
5. **Copy the phone number** (format: +1234567890)

### **4. Twilio Values for Netlify**
```
SMS_API_KEY=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SMS_FROM_NUMBER=+1234567890
```

---

## 🆔 **Aadhaar KYC Provider Setup**

### **Option 1: UIDAI Authorized Provider**
**Official KYC Providers for Aadhaar:**
- **Karza**: https://www.karza.in/
- **SignDesk**: https://www.signdesk.in/
- **Onfido**: https://onfido.com/
- **Jumio**: https://www.jumio.com/

### **Option 2: Demo/Testing Provider**
**For Development:**
- **Aadhaar Bridge**: https://aadhaarbridge.com/
- **DigiLocker**: https://digitallocker.gov.in/

### **How to Get API Key:**
1. **Choose a provider** from above
2. **Register as business/developer**
3. **Complete KYC verification** (required for Aadhaar services)
4. **Request API access** for "Aadhaar e-KYC"
5. **Get API credentials** from developer dashboard

### **Aadhaar API Values for Netlify**
```
AADHAAR_API_BASE_URL=https://api.karza.in/v2
AADHAAR_API_KEY=your-karza-api-key-here
```

---

## 🚀 **Step-by-Step Setup**

### **Step 1: Twilio Setup (5 minutes)**
```bash
# 1. Create account at https://www.twilio.com/
# 2. Get free trial credits
# 3. Buy a phone number ($1/month)
# 4. Copy Auth Token and Phone Number
```

### **Step 2: KYC Provider Setup (1-2 days)**
```bash
# 1. Choose provider (Karza recommended)
# 2. Submit business documents
# 3. Complete provider verification
# 4. Get API access for Aadhaar e-KYC
# 5. Copy API credentials
```

### **Step 3: Update Netlify Variables**
```bash
# Add to Netlify Environment Variables:
SMS_API_KEY=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SMS_FROM_NUMBER=+1234567890
AADHAAR_API_BASE_URL=https://api.karza.in/v2
AADHAAR_API_KEY=your-karza-api-key-here
```

---

## 💰 **Cost Information**

### **Twilio SMS Costs**
- **Free Trial**: $15 credit
- **SMS Messages**: ~$0.0079 per message
- **Phone Number**: $1/month
- **Monthly Cost**: ~$5-10 for 1000 OTPs

### **KYC Provider Costs**
- **Setup Fee**: $500-1000 (one-time)
- **Per Verification**: $2-5 per Aadhaar verification
- **Monthly Minimum**: $50-100

---

## 🏢 **Recommended Providers**

### **For Production:**
1. **Twilio** (SMS) - Reliable, global coverage
2. **Karza** (Aadhaar) - Indian KYC specialist
3. **DigiLocker** (Aadhaar) - Government official

### **For Development:**
1. **Twilio Trial** - Free credits for testing
2. **Aadhaar Bridge** - Demo API for development
3. **Mock Services** - Local testing without real APIs

---

## 📋 **Quick Setup Checklist**

### **Twilio Checklist**
- [ ] Create Twilio account
- [ ] Verify email and phone
- [ ] Get free trial credits
- [ ] Buy SMS-enabled phone number
- [ ] Copy Auth Token
- [ ] Copy Phone Number

### **KYC Provider Checklist**
- [ ] Choose KYC provider
- [ ] Submit business documents
- [ ] Complete verification process
- [ ] Get API access
- [ ] Copy API credentials
- [ ] Test API endpoints

---

## 🔧 **Testing Before Deployment**

### **Test Twilio SMS**
```python
# Test SMS sending
from twilio.rest import Client
client = Client(account_sid, auth_token)
message = client.messages.create(
    body="Test OTP: 123456",
    from_="+1234567890",
    to="+91XXXXXXXXXX"
)
```

### **Test Aadhaar API**
```python
# Test Aadhaar verification
import requests
response = requests.post(
    "https://api.karza.in/v2/aadhaar-otp",
    json={"aadhaar": "123456789012"},
    headers={"Authorization": "Bearer your-api-key"}
)
```

---

## 🎯 **Final Values for Netlify**

Once you complete setup, your Netlify variables will look like:

```
SMS_API_KEY=AC1234567890abcdef1234567890abcdef
SMS_FROM_NUMBER=+1234567890
AADHAAR_API_BASE_URL=https://api.karza.in/v2
AADHAAR_API_KEY=kz_live_1234567890abcdef1234567890abcdef
```

---

**Setup Time:** 1-2 days (KYC provider verification)  
**Monthly Cost:** ~$10-20 (SMS + KYC)  
**Support:** 24/7 available from providers
