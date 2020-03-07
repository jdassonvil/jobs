import jinja2
import os
import smtplib
import ssl

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

def send_email(jobs):
    port = 465  # For SSL
    password = os.getenv("EMAIL_PASSWORD")
    email = "plusfortquelesplusfort@gmail.com"

    # Create a secure SSL context
    context = ssl.create_default_context()
    sender_email = email
    receiver_email = "mathilde.canales@gmail.com"
    message = MIMEMultipart("alternative")
    message["Subject"] = "Jobs en vue !"
    message["From"] = sender_email
    message["To"] = receiver_email

    plain = """\
Subject: Hi there

This message is sent from Python."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.join(ROOT_DIR, "templates"))
    )

    template = env.get_template('email.tpl')
    html = template.render(jobs=jobs)

    part1 = MIMEText(plain, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)


    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

    print("email sent to {}".format(receiver_email))

