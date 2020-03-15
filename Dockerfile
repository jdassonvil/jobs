# source: https://www.blazemeter.com/blog/how-to-run-selenium-tests-in-docker/
FROM python:3.7

# gconf-gsettings-backend replace libgconf2-4
RUN apt-get update && apt-get install -yq \
    chromium=79.0.3945.130-1~deb10u1 \
    git-core \
    xvfb \
    xsel \
    unzip \
    gconf-gsettings-backend \
    libncurses5 \
    libxml2-dev \
    libxslt-dev \
    libz-dev \
    xclip

RUN wget -q "https://github.com/mozilla/geckodriver/releases/download/v0.26.0/geckodriver-v0.26.0-linux64.tar.gz" -O /tmp/geckodriver.tgz \
    && tar zxf /tmp/geckodriver.tgz -C /usr/bin/ \
        && rm /tmp/geckodriver.tgz

# chromeDriver v2.35
RUN wget -q "https://chromedriver.storage.googleapis.com/79.0.3945.36/chromedriver_linux64.zip" -O /tmp/chromedriver.zip \
    && unzip /tmp/chromedriver.zip -d /usr/bin/ \
    && rm /tmp/chromedriver.zip

# xvfb - X server display
ADD xvfb-chromium /usr/bin/xvfb-chromium
RUN ln -s /usr/bin/xvfb-chromium /usr/bin/google-chrome \
    && chmod 777 /usr/bin/xvfb-chromium

# create symlinks to chromedriver and geckodriver (to the PATH)
RUN ln -s /usr/bin/geckodriver /usr/bin/chromium-browser \
    && chmod 777 /usr/bin/geckodriver \
    && chmod 777 /usr/bin/chromium-browser


LABEL "com.datadoghq.ad.logs"='[{"source": "python", "service": "jobsearch", "sourcecategory": "sourcecode"}]'

ADD requirements.txt /tmp
RUN pip3 install -r /tmp/requirements.txt
RUN mkdir /opt/app /etc/jobs
ADD app /opt/app
ADD BLACKLIST /etc/jobs/BLACKLIST
ENV CONFIG_DIR /etc/jobs

WORKDIR /opt

ENTRYPOINT [ "python3", "-m", "app.main" ]
