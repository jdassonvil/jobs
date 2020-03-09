import os

def load_blacklist():
    blacklist_filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "BLACKLIST")
    keyword_blacklist = []
    with open(blacklist_filepath) as f:
        for line in f:
            if line != "":
                keyword_blacklist.append(line.lower().strip())

    return keyword_blacklist
