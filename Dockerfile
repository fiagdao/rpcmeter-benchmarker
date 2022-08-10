FROM postgres:latest

# install Python 3
RUN apt-get update && apt-get install -y python3 python3-pip
RUN apt-get -y install python3-dev

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY requirements.txt /code/
RUN pip install -r requirements.txt

COPY . /code/
