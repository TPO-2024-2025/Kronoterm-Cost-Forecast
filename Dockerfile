FROM homeassistant/home-assistant

# after updating this file also update compose.yml

RUN apk add --no-cache alpine-sdk

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

RUN apk del alpine-sdk