# start by pulling the python image
FROM python:3.8-slim-buster

COPY . /app 

WORKDIR /app

# install the dependencies and packages in the requirements file
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 80

# configure the container to run in an executed manner
CMD ["python","server.py"]
