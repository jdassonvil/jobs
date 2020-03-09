import os

def load_blacklist():
    config_dir = os.getenv("CONFIG_DIR") if os.getenv("CONFIG_DIR") else os.path.dirname(os.path.dirname(__file__))
    blacklist_filepath = os.path.join(config_dir, "BLACKLIST")
    keyword_blacklist = []
    with open(blacklist_filepath) as f:
        for line in f:
            if line != "":
                keyword_blacklist.append(line.lower().strip())

    return keyword_blacklist
