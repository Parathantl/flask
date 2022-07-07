sudo add-apt-repository ppa:deadsnakes/ppa

sudo apt-get update

sudo apt-get install python3.8

sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1

cd /usr/lib/python3/dist-packages

sudo cp apt_pkg.cpython-310-x86_64-linux-gnu.so apt_pkg.so

sudo apt install python3-pip

sudo apt-get install python3.8-distutils