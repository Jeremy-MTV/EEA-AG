import smtplib
import os
from dotenv import load_dotenv

load_dotenv('.env')

server = "ssl0.ovh.net"
port = 587
user = os.environ.get('MAIL_USERNAME')
pwd = os.environ.get('MAIL_PASSWORD')

try:
    print(f"Connecting to {server}:{port}...")
    smtp = smtplib.SMTP(server, port)
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    print("STARTTLS successful. Authenticating...")
    smtp.login(user, pwd)
    print("Authentication successful!")
    smtp.quit()
except Exception as e:
    print("Error:", e)
