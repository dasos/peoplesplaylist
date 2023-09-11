FROM python:3.9

RUN apt-get update -qq \
    && apt-get -y --no-install-recommends install libssl-dev python3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get -qq autoremove \
    && apt-get -qq clean

WORKDIR /usr/src/

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

ENV PYTHONUNBUFFERED=1

EXPOSE 8080

ENTRYPOINT python3 web_app/app.py
