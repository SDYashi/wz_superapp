import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailNotifier:
    def __init__(self, username, password, smtp_server, smtp_port):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def send_email(self, recipient_email, subject, message):
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = recipient_email
        msg['Subject'] = subject

        # Attach the message body
        msg.attach(MIMEText(message, 'plain'))

        try:
            # Establish connection to the mail server
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.set_debuglevel(1)  # Optional: debug mode to see communication
                server.ehlo()  # Send EHLO command to the server
                # Attempt LOGIN authentication instead of CRAM-MD5
                server.login(self.username, self.password)  # Using LOGIN authentication
                server.sendmail(self.username, recipient_email, msg.as_string())
            print(f"Email sent successfully to {recipient_email}")
        except smtplib.SMTPAuthenticationError as e:
            print(f"Authentication failed: {e}")
        except smtplib.SMTPException as e:
            print(f"SMTP error occurred: {e}")
        except Exception as e:
            print(f"Failed to send email: {e}")

if __name__ == "__main__":
    username = 'teamfilestore@rediffmail.com'
    password = 'SDeepak#123456'  # Consider using environment variables instead
    smtp_server = 'smtp.rediffmail.com'
    smtp_port = 465  # For SSL connection

    notifier = EmailNotifier(username, password, smtp_server, smtp_port)
    
    try:
        # Establish the connection and send an email
        recipient_email = 'deepakmarskole88@gmail.com'
        subject = 'Server Issue Notification'
        message = 'Dear User,\n\nWe are experiencing some issues with the API. Please check our server.\n\nBest regards,\nYour Super App Team'
        
        print(f"Connecting to the email server {smtp_server}...")
        notifier.send_email(recipient_email, subject, message)
    except Exception as e:
        print(f"Error while trying to send the email: {e}")
