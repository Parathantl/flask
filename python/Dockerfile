# start by pulling the python image
FROM python:3.8-slim-buster

# switch working directory
WORKDIR /app

ADD . /app

# install the dependencies and packages in the requirements file
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

EXPOSE 5000

# configure the container to run in an executed manner
CMD ["python3","server.py"]
