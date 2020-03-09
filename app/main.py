import logging
import re
import os
import sys
import time

from collections import namedtuple
from pymongo import MongoClient
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from .notifications.email import EmailNotifier
from .config import load_blacklist

Job = namedtuple('Job', 'company title contract location href timestamp')


LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"

SECONDES_REGEX = re.compile('il y a ([0-9]{1,2}) seconde[s]?')
MINUTES_REGEX = re.compile('il y a ([0-9]{1,2}) minute[s]?')
HOURS_REGEX = re.compile('il y a ([0-9]{1,2}) heure[s]?')
DAYS_REGEX = re.compile('il y a ([0-9]{1,2}) jour[s]?')

JOB_URL_REGEX = re.compile('(.+)\/companies\/(.+)\/jobs\/(.+)')
START_TS=int(datetime.now().timestamp())

URL_PATTERN="https://www.welcometothejungle.com/fr/jobs?refinementList%5Bcontract_type_names.fr%5D%5B%5D=CDD%20%2F%20Temporaire&refinementList%5Bcontract_type_names.fr%5D%5B%5D=CDI&refinementList%5Borganization.size.fr%5D%5B%5D=%3C%2015%20salari%C3%A9s&refinementList%5Borganization.size.fr%5D%5B%5D=Entre%2015%20et%2050%20salari%C3%A9s&refinementList%5Borganization.size.fr%5D%5B%5D=Entre%2050%20et%20250%20salari%C3%A9s&page={}"


def can_renotify(notify_ts: int):
    # TODO: when should we renotify ?
    return False

def filter_jobs(jobs):
    filtered_jobs = []
    keyword_blacklist = load_blacklist()
    for job in jobs:
        excluded = False
        for word in KEYWORD_BLACKLIST:
            if word in job['title'].lower():
                excluded = True
                continue
        if job['contract'].lower() == "stage":
            excluded = True
        if 'notify_ts' in job and not can_renotify(job['notify_ts']):
            excluded = True
        if not excluded:
            filtered_jobs.append(job)
    return filtered_jobs


def compute_job_ts(time_text):
    minutes_ago = None
    ts = None
    if SECONDES_REGEX.match(time_text):
        m = SECONDES_REGEX.match(time_text)
        minutes_ago = int(m.group(1))
    if MINUTES_REGEX.match(time_text):
        m = MINUTES_REGEX.match(time_text)
        minutes_ago = int(m.group(1)) * 60
    elif HOURS_REGEX.match(time_text):
        m = HOURS_REGEX.match(time_text)
        minutes_ago = int(m.group(1)) * 60 * 60
    elif DAYS_REGEX.match(time_text):
        m = DAYS_REGEX.match(time_text)
        minutes_ago = int(m.group(1)) * 24 * 60 * 60
    elif time_text == "hier":
        minutes_ago = 86400
    elif time_text == "avant-hier":
        minutes_ago = 172800
    else:
        logging.warning("Date not extracted: {}".format(time_text))
    if minutes_ago:
        ts = int(START_TS) - minutes_ago
    return ts

def extract_href(c):
    for link in c.find_elements_by_tag_name("a"):
        href=link.get_attribute("href")
        if JOB_URL_REGEX.match(href):
            return href
    return ""

def notify(notify_window: int):
    notifier = EmailNotifier(os.getenv("EMAIL_PASSWORD"), os.getenv("EMAIL_RECEIVER"))
    client = MongoClient()
    client = MongoClient('localhost', 27017)
    jobs_collection = client.jobs.jobs

    job_updates = []
    jobs = filter_jobs(jobs_collection.find({ "timestamp": { "$gt": START_TS - notify_window }}))

    if len(jobs) == 0:
        logging.info("No new job offers")
        return

    for job in jobs:
        job_updates.append(job)
        jobs_collection.update_one({ "_id": job["_id"]}, {"$set": {"notify_ts": START_TS}})

    notifier.send(job_updates)

def ingest(job: Job):
    client = MongoClient()
    client = MongoClient('localhost', 27017)
    jobs_collection = client.jobs.jobs
    doc = jobs_collection.find_one({"company": job.company, "title": job.title})
    if doc is None:
        jobs_collection.insert_one(job._asdict())
        logging.debug("{} is new".format(job.title))
    else:
        logging.debug("{} already exist".format(job.title))

def fetch_jobs(driver, max_time_window: int):
    last_ts = START_TS
    page = 1
    while START_TS - last_ts < max_time_window: #other conditions ?
        url=URL_PATTERN.format(page)
        logging.info("Looking at {}".format(url))
        driver.get(url)
        time.sleep(5) # Wait 5 seconds for the page to be loaded
        companies=driver.find_elements_by_tag_name("article")
        page = page + 1

        for c in companies:
            content=str(c.text)
            href = extract_href(c)
            items=content.splitlines()
            if len(items) >= 5:
                job=Job(items[0], items[1], items[2], items[3], href, compute_job_ts(items[4]))
                if job.timestamp is not None:
                    ingest(job)
                    if job.timestamp < last_ts:
                        last_ts = job.timestamp
            else:
                logging.warning("Missing fields in job offer")

def main():
    # For how far in the past we scroll the website
    #max_time_window=86400 # 24h
    max_time_window = int(os.getenv("MAX_TIME_WINDOW_S", 3600)) # By default 1h
    # After how long an offer that has been reposted will be re notified
    renotify_window=604800 # 1 week
    notify_window=86400 # 24h
    driver = webdriver.Chrome()
    driver.implicitly_wait(60)
    logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)

    try:
        fetch_jobs(driver, max_time_window)
        notify(notify_window)
    finally:
        driver.close()

if __name__ == "__main__":
   main()
