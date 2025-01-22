FROM ubuntu:20.04

# system basics
RUN apt-get update && apt-get -y install build-essential curl python3 python3-pip libffi-dev

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

COPY server.py start.sh master volume test.py /tmp/