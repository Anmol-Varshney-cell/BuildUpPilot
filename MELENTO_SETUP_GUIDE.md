# Melento Aadhaar KYC API Setup Guide

## 🚀 **Step-by-Step Setup for Melento**

### **Step 1: Access Melento Website**
1. **Go to**: https://melento.ai/
2. **Click "Get Started"** or "Talk to Sales"
3. **Choose "Aadhaar Verification API"**
4. **Fill business details**:
   - Company name
   - Business type
   - Contact information
   - Expected monthly volume

### **Step 2: Get API Credentials**
1. **Complete business verification** (1-2 days)
2. **Receive API access** from Melento team
3. **Get your API keys**:
   - API Endpoint URL
   - Authentication token/key
   - Documentation access

### **Step 3: Test API Integration**
```python
# Test Melento API
import requests

# Your API credentials from Melento
API_BASE_URL = "https://api.melento.ai/v2"
API_KEY = "your-melento-api-key-here"

# Test Aadhaar verification
def test_aadhaar_verification(aadhaar_number):
    payload = {
        "aadhaar_number": aadhaar_number,
        "consent": "I consent to Aadhaar verification"
    }
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/aadhaar/verify",
        json=payload,
        headers=headers
    )
    
    return response.json()

# Test with sample Aadhaar
result = test_aadhaar_verification("123456789012")
print(result)
```

### **Step 4: Update Netlify Environment Variables**
```
AADHAAR_API_BASE_URL=https://api.melento.ai/v2
AADHAAR_API_KEY=your-melento-api-key-here
```

---

## 🔧 **How Melento API Works**

### **Verification Process**
1. **User enters** Aadhaar number in your app
2. **System generates** OTP request to Melento
3. **Melento sends** OTP to user's registered mobile
4. **User receives** OTP and enters it
5. **Melento verifies** OTP with UIDAI
6. **System receives** KYC data (name, DOB, address)
7. **Account verified** - User can access full features

### **API Response Format**
```json
{
    "success": true,
    "data": {
        "name": "User Name",
        "date_of_birth": "1990-01-01",
        "gender": "M",
        "address": "Full Address",
        "pincode": "110001",
        "photo": "base64_encoded_photo"
    },
    "masked_aadhaar": "XXXX-XXXX-1234",
    "verification_id": "MEL_1234567890"
}
```

---

## 📋 **Integration with BUILD UP PILOT**

### **Update Aadhaar Service**
```python
# In services/aadhaar_service.py
def send_otp(self, aadhaar_number):
    try:
        # Use Melento instead of generic API
        payload = {
            'aadhaar_number': aadhaar_number,
            'consent': 'I consent to Aadhaar verification',
            'purpose': 'Identity verification for career platform'
        }
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{self.api_base_url}/aadhaar/send-otp",
            json=payload,
            headers=headers,
            timeout=self.timeout
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Melento API error: {response.status_code}")
            return {
                'success': False,
                'error': 'Aadhaar verification service unavailable',
                'error_code': 'SERVICE_ERROR'
            }
            
    except Exception as e:
        logger.error(f"Melento request failed: {str(e)}")
        return {
            'success': False,
            'error': 'Failed to send OTP',
            'error_code': 'REQUEST_FAILED'
        }
```

### **Configuration Update**
```python
# In config.py
class Config:
    # Melento Configuration
    AADHAAR_API_BASE_URL = os.getenv('AADHAAR_API_BASE_URL', 'https://api.melento.ai/v2')
    AADHAAR_API_KEY = os.getenv('AADHAAR_API_KEY', 'your-melento-api-key-here')
```

---

## 🎯 **Complete Netlify Variables**

### **Add these to Netlify:**
```
# Melento Aadhaar KYC
AADHAAR_API_BASE_URL=https://api.melento.ai/v2
AADHAAR_API_KEY=your-melento-api-key-here

# Keep other variables
FLASK_ENV=production
SECRET_KEY=buildup-pilot-secret-key-2026
DATABASE_URL=sqlite:///buildup.db
DEMO_MODE=false
SMS_GATEWAY_URL=https://api.twilio.com/2010-04-01/Accounts
SMS_API_KEY=your-twilio-auth-token
SMS_FROM_NUMBER=+1234567890
SESSION_TYPE=filesystem
SESSION_PERMANENT=false
SESSION_USE_SIGNER=true
PERMANENT_SESSION_LIFETIME=3600
```

---

## 💰 **Pricing and Costs**

### **Melento Pricing Model**
- **Setup Fee**: Contact sales (typically $500-1000)
- **Per Verification**: $2-5 per Aadhaar KYC
- **Volume Discounts**: Available for high usage
- **Support**: 24/7 technical support

### **Monthly Cost Estimates**
- **100 Verifications**: ~$200-500/month
- **500 Verifications**: ~$1000-2500/month
- **1000 Verifications**: ~$2000-5000/month

---

## 📞 **Contact Melento Support**

### **Sales Team**
- **Email**: sales@melento.ai
- **Phone**: Available on website
- **Website**: https://melento.ai/
- **Response Time**: Usually 24-48 hours

### **Technical Support**
- **Documentation**: https://docs.melento.ai/
- **API Status**: https://status.melento.ai/
- **Developer Portal**: Available after signup

---

## ⚡ **Quick Setup Checklist**

### **Before Starting**
- [ ] Business registration documents ready
- [ ] Company PAN card
- [ ] Bank account details
- [ ] Contact information
- [ ] Expected monthly volume

### **After Signup**
- [ ] Receive API credentials
- [ ] Test API endpoints
- [ ] Update Netlify variables
- [ ] Deploy to production
- [ ] Monitor API usage

---

## 🔄 **Testing Process**

### **Development Testing**
1. **Use sandbox/test mode** if available
2. **Test with sample Aadhaar numbers**
3. **Verify API responses**
4. **Check error handling**
5. **Validate data format**

### **Production Testing**
1. **Use real Aadhaar numbers**
2. **Test complete user flow**
3. **Monitor success rates**
4. **Check billing**
5. **Set up alerts**

---

## 🎉 **Ready for Production**

Once you complete Melento setup:

1. ✅ **Get API credentials** from Melento
2. ✅ **Update environment variables** in Netlify
3. ✅ **Test integration** thoroughly
4. ✅ **Deploy to production**
5. ✅ **Monitor performance**

Your BUILD UP PILOT will have professional, reliable Aadhaar KYC with Melento's industry-leading API service.

---

**Setup Time**: 1-3 days  
**Cost**: $2-5 per verification  
**Support**: 24/7 available  
**Reliability**: Enterprise-grade
