import smtplib

try:
    with smtplib.SMTP_SSL('smtp.rediffmail.com', 465) as server:
        server.ehlo() 
        print("Connection successful")
except Exception as e:
    print(f"Failed to connect: {e}")