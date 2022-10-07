sudo docker image build -t flask-python .

sudo  docker run -p 80:80 --net=host flask-python
