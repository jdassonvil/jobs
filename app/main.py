import logging
import re
import os
import sys
import time

from pymongo import MongoClient
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from .notifications.email import EmailNotifier
from .config import load_blacklist
from .model import Job, from_mongo_doc
from .dd import Stats
from .log import init_logger

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
        for word in keyword_blacklist:
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
    docs = filter_jobs(jobs_collection.find({ "timestamp": { "$gt": START_TS - notify_window }}))

    if len(jobs) == 0:
        logging.info("No new job offers")
        return

    for doc in docs:
        job = from_mongo_doc(job)
        job_updates.append(job)
        Stats.record_notification(job)
        jobs_collection.update_one({ "_id": doc["_id"]}, {"$set": {"notify_ts": START_TS}})

    notifier.send(job_updates)

def ingest(job: Job):
    client = MongoClient()
    client = MongoClient('localhost', 27017)
    jobs_collection = client.jobs.jobs
    doc = jobs_collection.find_one({"company": job.company, "title": job.title})
    count_new = 0
    if doc is None:
        jobs_collection.insert_one(job._asdict())
        logging.info("{} is new".format(job.title))
        Stats.record_new_job(job)
        count_new = count_new + 1
    else:
        logging.debug("{} already exist".format(job.title))
        last_ts = doc["last_ts"] if "last_ts" in doc else doc["timestamp"]
        jobs_collection.update_one({ "_id": doc["_id"]}, {"$set": {"last_ts": START_TS}})
        # It's a repost if the same job come back more than 12h after its first occurence
        if last_ts < START_TS - (12 * 60 * 60):
            logging.info("{} has been reposted (first time: {}, last time: {})".format(job.title, job.timestamp, last_ts))
            Stats.record_old_job(job)

def fetch_jobs(driver, max_time_window: int):
    last_ts = START_TS
    page = 1
    while START_TS - last_ts <= max_time_window: #other conditions ?
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
                job=Job(items[0], items[1], items[2], items[3], href, compute_job_ts(items[4]), items[4])
                Stats.record_view_job(job)
                if job.timestamp is not None:
                    ingest(job)
                    if job.timestamp < last_ts:
                        last_ts = job.timestamp
            else:
                logging.warning("Missing fields in job offer")

def main():
    init_logger()
    # For how far in the past we scroll the website
    #max_time_window=86400 # 24h
    max_time_window = int(os.getenv("MAX_TIME_WINDOW_S", 3600)) # By default 1h
    logging.info("Max time window: {}".format(max_time_window))
    # After how long an offer that has been reposted will be re notified
    renotify_window=604800 # 1 week
    notify_window=86400 # 24h

    if len(sys.argv) < 2:
        logging.error("missing command")
        sys.exit(1)

    try:
        driver = webdriver.Chrome()
        driver.implicitly_wait(60)

        if sys.argv[1] == "notify":
            notify(notify_window)
        if sys.argv[1] == "search":
            fetch_jobs(driver, max_time_window)
        # Make sure we the statsd buffer has been flushed
        # TODO: figure out how to make this properly
        time.sleep(10)
    finally:
        driver.close()

if __name__ == "__main__":
   main()
