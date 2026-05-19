# Netlify Deployment Settings for BUILD UP PILOT

## ⚠️ **Important Notice**
BUILD UP PILOT is a **Flask backend application** with database and server-side functionality. Netlify is primarily designed for **static sites**. For full functionality, you'll need to use Netlify Functions or consider alternative hosting.

---

## **🔧 Netlify Build Settings (Line by Line)**

### **Branch to deploy**
```
main
```

### **Base directory**
```
/
```
*Note: Root directory since Flask app is at project root*

### **Build command**
```
echo "No build needed for Flask backend"
```
*Note: Flask apps don't need frontend build process*

### **Publish directory**
```
static
```
*Note: Static files directory for CSS, JS, images*

### **Functions directory**
```
netlify/functions
```
*Note: For serverless Flask deployment*

---

## **🌐 Environment Variables (Line by Line)**

### **Required for Production**
```
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_URL=your-production-database-url
DEMO_MODE=false
```

### **SMS Gateway Configuration**
```
SMS_GATEWAY_URL=https://api.twilio.com/2010-04-01/Accounts
SMS_API_KEY=your_twilio_auth_token
SMS_FROM_NUMBER=+1234567890
```

### **Aadhaar KYC Configuration**
```
AADHAAR_API_BASE_URL=https://api.kycprovider.com
AADHAAR_API_KEY=your_aadhaar_api_key_here
```

### **Session Configuration**
```
SESSION_TYPE=filesystem
SESSION_PERMANENT=false
SESSION_USE_SIGNER=true
PERMANENT_SESSION_LIFETIME=3600
```

### **Sandbox Configuration**
```
SANDBOX_MODE=true
SANDBOX_API_KEY=your-sandbox-api-secret-here
SANDBOX_API_URL=https://sandbox.co.in/api/v2
```

---

## **📁 Required Files for Netlify**

### **1. netlify.toml Configuration**
```toml
[build]
  base = "/"
  command = "echo 'Flask backend - no build needed'"
  publish = "static"
  functions = "netlify/functions"

[build.environment]
  FLASK_ENV = "production"
  PYTHON_VERSION = "3.9"

[[redirects]]
  from = "/api/*"
  to = "/.netlify/functions/:splat"
  status = 200

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 404
```

### **2. requirements.txt for Functions**
```txt
Flask==2.3.3
Flask-Login==0.6.3
Flask-SQLAlchemy==3.0.5
requests==2.31.0
python-dotenv==1.0.0
Werkzeug==2.3.7
```

### **3. netlify/functions/api.py (Serverless Flask)**
```python
import json
from flask import Flask, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Your Flask routes here
@app.route('/auth/login', methods=['POST'])
def login():
    # Your login logic
    return json.dumps({"success": True})

def handler(event, context):
    return app(event, context)
```

---

## **🚀 Deployment Options**

### **Option 1: Netlify Functions (Recommended)**
1. Convert Flask routes to Netlify Functions
2. Use serverless database (MongoDB Atlas, etc.)
3. Deploy static files to Netlify
4. Functions handle API calls

### **Option 2: Alternative Hosting (Better for Flask)**
- **Heroku**: Full Flask support
- **PythonAnywhere**: Python hosting
- **DigitalOcean**: VPS with full control
- **AWS EC2**: Cloud server deployment

### **Option 3: Hybrid Approach**
- **Frontend**: Netlify (static HTML/CSS/JS)
- **Backend**: Separate server (Heroku, PythonAnywhere)
- **Database**: Cloud database service

---

## **📋 Step-by-Step Netlify Setup**

### **1. Prepare Project**
```bash
# Create netlify directory structure
mkdir -p netlify/functions
cp -r static netlify/
cp templates/*.html netlify/static/
```

### **2. Create Functions**
```bash
# Convert Flask routes to serverless functions
# Each route becomes a separate function file
touch netlify/functions/auth.py
touch netlify/functions/admin.py
touch netlify/functions/users.py
```

### **3. Configure netlify.toml**
```bash
# Create netlify.toml in root
touch netlify.toml
# Add configuration from above
```

### **4. Deploy to Netlify**
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login and deploy
netlify login
netlify init
netlify deploy --prod
```

---

## **⚡ Quick Netlify Settings Summary**

### **Build Settings**
- **Branch**: `main`
- **Base directory**: `/`
- **Build command**: `echo "Flask backend - no build needed"`
- **Publish directory**: `static`
- **Functions directory**: `netlify/functions`

### **Environment Variables**
- `FLASK_ENV=production`
- `SECRET_KEY=your-secret-key`
- `DATABASE_URL=your-db-url`
- `DEMO_MODE=false`
- `SMS_GATEWAY_URL=your-sms-url`
- `SMS_API_KEY=your-sms-key`
- `SMS_FROM_NUMBER=your-phone-number`

---

## **🎯 Recommendation**

**For Full BUILD UP PILOT Functionality**: Consider **Heroku** or **PythonAnywhere** instead of Netlify, as they provide complete Flask backend support with database and SMS integration.

**For Frontend Only**: Use Netlify for static files and deploy backend separately.

---

*Last Updated: May 6, 2026*
