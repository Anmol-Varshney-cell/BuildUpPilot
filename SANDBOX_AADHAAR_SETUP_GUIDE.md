# Sandbox Aadhaar KYC API Setup Guide

## 🚀 **Step-by-Step Sandbox Setup**

### **Step 1: Access Sandbox Platform**
1. **Go to**: https://sandbox.co.in/
2. **Click "Get Started"** button
3. **Choose "KYC Services"**
4. **Select "Aadhaar Verification"**

### **Step 2: Create Account**
1. **Click "Sign Up"** (top right)
2. **Fill registration form**:
   - Business name
   - Business type
   - Contact email
   - Phone number
   - Business address
3. **Verify email** (check inbox)
4. **Set password** for your account

### **Step 3: Complete Business Verification**
1. **Submit business documents**:
   - Business registration certificate
   - PAN card
   - Address proof
2. **Wait for approval** (1-2 business days)
3. **Receive confirmation** email

### **Step 4: Access API Dashboard**
1. **Login** to Sandbox dashboard
2. **Go to "API Documentation"**
3. **Find "Aadhaar Verification API"**
4. **Click "Get API Keys"**

### **Step 5: Generate API Credentials**
1. **Create new API key**:
   - Name your API key (e.g., "BUILDUP_PILOT_AADHAAR")
   - Select permissions (Aadhaar verification only)
2. **Copy API credentials**:
   - API Endpoint URL
   - API Key/Secret
   - Documentation link

---

## 🔧 **Sandbox API Configuration**

### **API Endpoint**
```
https://sandbox.co.in/api/v2/aadhaar/verify
```

### **Authentication**
```
Headers:
Authorization: Bearer YOUR_SANDBOX_API_KEY
Content-Type: application/json
```

### **Request Format**
```json
{
    "aadhaar_number": "123456789012",
    "consent": "I consent to Aadhaar verification for identity confirmation"
}
```

### **Response Format**
```json
{
    "success": true,
    "data": {
        "name": "User Name",
        "date_of_birth": "1990-01-01",
        "gender": "M",
        "address": "Full Address Details",
        "pincode": "110001",
        "masked_aadhaar": "XXXX-XXXX-1234",
        "photo": "base64_encoded_photo"
    },
    "verification_id": "SANDBOX_1234567890"
}
```

---

## 🧪 **Testing Sandbox API**

### **Python Test Code**
```python
import requests
import json

# Sandbox API Configuration
SANDBOX_API_URL = "https://sandbox.co.in/api/v2/aadhaar/verify"
SANDBOX_API_KEY = "your-sandbox-api-key-here"

def test_sandbox_aadhaar(aadhaar_number):
    """Test Aadhaar verification with Sandbox"""
    
    payload = {
        "aadhaar_number": aadhaar_number,
        "consent": "I consent to Aadhaar verification for identity confirmation"
    }
    
    headers = {
        "Authorization": f"Bearer {SANDBOX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            SANDBOX_API_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        return response.json()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

# Test with sample Aadhaar
result = test_sandbox_aadhaar("123456789012")
if result:
    print("✅ Sandbox API working!")
else:
    print("❌ Sandbox API failed!")
```

### **Test with cURL**
```bash
curl -X POST https://sandbox.co.in/api/v2/aadhaar/verify \
  -H "Authorization: Bearer YOUR_SANDBOX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "aadhaar_number": "123456789012",
    "consent": "I consent to Aadhaar verification for identity confirmation"
  }'
```

---

## 🌐 **Sandbox Features**

### **Available Services**
- ✅ **Aadhaar OTP Verification**
- ✅ **Aadhaar Demographic Verification**
- ✅ **Consent-based Verification**
- ✅ **Masked Aadhaar Response**
- ✅ **Real-time API Access**

### **Benefits of Sandbox**
- 🧪 **Free Testing**: No charges during development
- 🔧 **Full API Access**: Test all endpoints
- 📊 **API Documentation**: Complete integration guides
- 🛡️ **Safe Environment**: No real data affected
- ⚡ **Instant Setup**: No business verification required

---

## 📋 **Sandbox vs Production**

| Feature | Sandbox | Production |
|----------|----------|------------|
| **Cost** | Free | Pay per use |
| **Setup Time** | Instant | 1-2 days |
| **API Access** | Immediate | After approval |
| **Data** | Test data | Real data |
| **Support** | Documentation | 24/7 support |

---

## 🔧 **Integration with BUILD UP PILOT**

### **Update Aadhaar Service**
```python
# In services/aadhaar_service.py
def send_otp(self, aadhaar_number):
    try:
        # Use Sandbox API for development
        if current_app.config.get('SANDBOX_MODE', True):
            api_url = "https://sandbox.co.in/api/v2/aadhaar/send-otp"
            api_key = os.getenv('SANDBOX_API_KEY')
        else:
            api_url = "https://api.melento.ai/v2/aadhaar/send-otp"
            api_key = os.getenv('AADHAAR_API_KEY')
        
        payload = {
            'aadhaar_number': aadhaar_number,
            'consent': 'I consent to Aadhaar verification'
        }
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=self.timeout
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API error: {response.status_code}")
            return {
                'success': False,
                'error': 'Aadhaar verification service unavailable',
                'error_code': 'SERVICE_ERROR'
            }
            
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
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
    # Sandbox Configuration
    SANDBOX_MODE = os.getenv('SANDBOX_MODE', 'True')
    SANDBOX_API_KEY = os.getenv('SANDBOX_API_KEY', 'your-sandbox-api-key-here')
    SANDBOX_API_URL = os.getenv('SANDBOX_API_URL', 'https://sandbox.co.in/api/v2')
    
    # Production Configuration (for later)
    AADHAAR_API_BASE_URL = os.getenv('AADHAAR_API_BASE_URL', 'https://api.melento.ai/v2')
    AADHAAR_API_KEY = os.getenv('AADHAAR_API_KEY', 'your-melento-api-key-here')
```

---

## 📋 **Netlify Environment Variables**

### **Sandbox Configuration**
```
# Sandbox Mode (for development)
SANDBOX_MODE=true
SANDBOX_API_KEY=your-sandbox-api-key-here
SANDBOX_API_URL=https://sandbox.co.in/api/v2

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

## 🎯 **Quick Start Checklist**

### **Before Starting**
- [ ] Create Sandbox account
- [ ] Complete business verification
- [ ] Get API credentials
- [ ] Test API endpoints
- [ ] Update BUILD UP PILOT code

### **Testing Process**
- [ ] Test OTP sending
- [ ] Test verification flow
- [ ] Check response format
- [ ] Verify error handling

### **Ready for Production**
- [ ] Switch to production API
- [ ] Update environment variables
- [ ] Deploy to Netlify
- [ ] Monitor live performance

---

## 📞 **Sandbox Support**

### **Documentation**
- **API Docs**: https://developer.sandbox.co.in/
- **API Reference**: https://developer.sandbox.co.in/reference/
- **Integration Guides**: https://developer.sandbox.co.in/docs/
- **Status Page**: https://status.api.sandbox.co.in/

### **Contact**
- **Email**: support@sandbox.co.in
- **Help Center**: https://help.sandbox.co.in/
- **Sales**: https://sandbox.co.in/contact-sales/

---

## 🚀 **Production Migration**

When ready for production:

1. **Get production API** (Melento or other provider)
2. **Update environment variables**:
   ```
   SANDBOX_MODE=false
   AADHAAR_API_BASE_URL=https://api.melento.ai/v2
   AADHAAR_API_KEY=your-production-api-key
   ```
3. **Test with real data**
4. **Deploy to production**

---

**Setup Time**: 30 minutes  
**Cost**: Free (Sandbox)  
**Next Step**: Production API when ready
