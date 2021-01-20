import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Notifier:
    def __init__(self, email, password, recipients) -> None:
        self.email = email
        self.password = password
        self.recipients = recipients

    def sendEmail(self, subject, content) -> None:
        port = 465
        context = ssl.create_default_context()
        message = MIMEMultipart("alternative")
        message["Subject"] = f"ASP VM: {subject}"
        message["From"] = self.email

        message.attach(MIMEText(content, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(self.email, self.password)
            for recipient in self.recipients:
                message['To'] = recipient
                server.sendmail(self.email, recipient, message.as_string())
