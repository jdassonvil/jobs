from collections import namedtuple

Job = namedtuple('Job', 'company title contract location href timestamp timetext')

def from_mongo_doc(doc):
    return Job(doc["company"], doc["title"], doc["contract"], doc["href"], doc["timestamp"], doc["timestamptext"])
