 FROM python:3.4
 ENV PYTHONUNBUFFERED 0
 RUN mkdir /code
 WORKDIR /code
 ADD . /code/
 RUN pip install -r requirements.txt
