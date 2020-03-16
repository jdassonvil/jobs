import jinja2
import logging
import os
import smtplib
import ssl

from collections import defaultdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

class EmailNotifier:

    def __init__(self, password: str, receivers: List[str]):
        if not password or password == "":
            raise Exception("Email password undefined")

        if not receivers or len(receivers) == 0:
            raise Exception("Receiver(s) email undefined")

        self.receivers = receivers
        self.password = password

    def _to_companies_map(self, jobs):
        companies = defaultdict(list)
        for job in jobs:
            companies[job.company].append(job)

        return companies

    def send(self, jobs):
        port = 465  # For SSL
        password = os.getenv("EMAIL_PASSWORD")
        sender_email = "plusfortquelesplusfort@gmail.com"

        # Create a secure SSL context
        context = ssl.create_default_context()
        message = MIMEMultipart("alternative")
        message["Subject"] = "Jobs en vue !"
        message["From"] = sender_email

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
            for receiver in self.receivers:
                server.login(sender_email, self.password)
                message["To"] = receiver
                server.sendmail(sender_email, receiver, message.as_string())

                logging.info("email sent to {}".format(receiver))

