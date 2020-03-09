import jinja2
import logging
import os
import smtplib
import ssl

from collections import defaultdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

class EmailNotifier:

    def __init__(self, password, receiver):
        if not password or password == "":
            raise Exception("Email password undefined")

        if not receiver or receiver == "":
            raise Exception("Receiver email undefined")

        self.receiver = receiver
        self.password = password

    def _to_companies_map(self, jobs):
        companies = defaultdict(list)
        for job in jobs:
            companies[job['company']].append(job)

        return companies

    def send(self, jobs):
        port = 465  # For SSL
        password = os.getenv("EMAIL_PASSWORD")
        email = "plusfortquelesplusfort@gmail.com"

        # Create a secure SSL context
        context = ssl.create_default_context()
        sender_email = self.receiver
        message = MIMEMultipart("alternative")
        message["Subject"] = "Jobs en vue !"
        message["From"] = sender_email
        message["To"] = self.receiver
        message["Cc"] = "dassonville.jerome@gmail.com"

        plain = """\
    Subject: Hi there

    This message is sent from Python."""
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.join(ROOT_DIR, "templates"))
        )

        template = env.get_template('email.tpl')
        html = template.render(companies=self._to_companies_map(jobs))

        part1 = MIMEText(plain, "plain")
        part2 = MIMEText(html, "html")
        message.attach(part1)
        message.attach(part2)

        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(email, self.password)
            server.sendmail(sender_email, self.receiver, message.as_string())

        logging.info("email sent to {}".format(self.receiver))

