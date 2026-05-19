import random
import time


def generate_demo_email_otp():
    return str(random.randint(100000, 999999))


def build_demo_email(to_email: str, otp: str):
    # demo mail content
    return {
        "to": to_email,
        "subject": "BUILD UP Pilot - Your Recruiter OTP",
        "body": f"Your OTP for recruiter verification is: {otp}. Valid for 10 minutes."
    }

