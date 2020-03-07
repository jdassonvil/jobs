import re
import sys

from collections import namedtuple
from pymongo import MongoClient
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from .notifications.email import send_email

Job = namedtuple('Job', 'company title contract location href timestamp')

# TODO: il y a 20 secondes
MINUTES_REGEX = re.compile('il y a ([0-9]{1,2}) minutes')
HOURS_REGEX = re.compile('il y a ([0-9]{1,2}) heure[s]?')
JOB_URL_REGEX = re.compile('(.+)\/companies\/(.+)\/jobs\/(.+)')
START_TS=int(datetime.now().timestamp())

def compute_job_ts(time_text):
    minutes_ago = None
    ts = None
    if MINUTES_REGEX.match(time_text):
        m = MINUTES_REGEX.match(time_text)
        minutes_ago = int(m.group(1)) * 60
    elif HOURS_REGEX.match(time_text):
        m = HOURS_REGEX.match(time_text)
        minutes_ago = int(m.group(1)) * 60 * 60
    else:
        print("WARNING: date not extracted {}".format(time_text))
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
# company blacklist
    client = MongoClient()
    client = MongoClient('localhost', 27017)
    jobs_collection = client.jobs.jobs

    job_updates = []

    for job in jobs_collection.find({ "timestamp": { "$gt": START_TS - notify_window }}):
        job_updates.append(job)
        jobs_collection.update_one({ "_id": job["_id"]}, {"$set": {"notify_ts": START_TS}})

    send_email(job_updates)

def ingest(job: Job):
    client = MongoClient()
    client = MongoClient('localhost', 27017)
    jobs_collection = client.jobs.jobs
    doc = jobs_collection.find_one({"company": job.company, "title": job.title})
    if doc is None:
        jobs_collection.insert_one(job._asdict())
        #print("{} is new".format(job.title))
    #else:
    #    print("{} already exist".format(job.title))

def fetch_jobs(driver, max_time_window: int):
    last_ts = START_TS
    page = 1
    while START_TS - last_ts < max_time_window: #other conditions ?
        driver.get("https://www.welcometothejungle.com/fr/jobs?page={}".format(page))
        print("Looking at https://www.welcometothejungle.com/fr/jobs?page={}".format(page))
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
                print("Missing fields in job offer")

def main():
    # For how far in the past we scroll the website
    #max_time_window=86400 # 24h
    max_time_window=3600 # 24h
    # After how long an offer that has been reposted will be re notified
    renotify_window=604800 # 1 week
    notify_window=86400 # 24h
    driver = webdriver.Chrome()
    driver.implicitly_wait(60)

    try:
        fetch_jobs(driver, max_time_window)
        notify(notify_window)
    finally:
        driver.close()

if __name__ == "__main__":
   main()
