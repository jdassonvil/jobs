import datadog
from .model import Job

options = {
    'datadog.statsd_host':'127.0.0.1',
    'datadog.statsd_port':8125
}

datadog.initialize(**options)


class Stats:

    @staticmethod
    def _build_tags(job: Job):
        return ["company:{}".format(job.company), "location:{}".format(job.location)]

    @staticmethod
    def record_old_job(job: Job):
        print(datadog.statsd.__class__)
        datadog.statsd.increment('jobs.old', tags=Stats._build_tags(job))

    @staticmethod
    def record_new_job(job: Job):
        datadog.statsd.increment('jobs.new', tags=Stats._build_tags(job))

    @staticmethod
    def record_notification(job: Job):
        datadog.statsd.increment('jobs.notified', tags=Stats._build_tags(job))

    def flush():
        datadog.statsd.close_buffer()
