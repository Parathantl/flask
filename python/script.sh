sudo apt-get remove docker docker-engine docker.io

sudo apt-get remove docker docker-engine docker.io

sudo apt install docker.io

sudo snap install docker

docker --version

sudo docker ps

#sudo docker image build -t flask-python .
#sudo  docker run -p 80:80 --net=host flask-python


# docker volume create elast_data
# sudo docker run -d -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" -v elast_data:/usr/share/elasticsearch/data docker.elastic.co/elasticsearch/elasticsearch:7.16.3

# curl -X GET "localhost:9200/"