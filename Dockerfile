FROM python:3.7.4-alpine3.10

RUN apk --update add build-base python3-dev
RUN pip install klein
RUN pip install redis