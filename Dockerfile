# FROM --platform=linux/amd64 ubuntu

# pyre works with ubuntu 20 or newer
FROM ubuntu:20.04

RUN ln -snf /usr/share/zoneinfo/$CONTAINER_TIMEZONE /etc/localtime && echo $CONTAINER_TIMEZONE > /etc/timezone

# RUN apt-get purge libappstream3
RUN apt-get update

# python 3.8 installed by one of the following packages
# install packages needed
RUN apt-get install -y vim
RUN apt-get install -y wget
RUN apt-get install unzip
RUN apt-get install -y git
RUN apt install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa

RUN apt install -y  expect

RUN apt-get install -y python3-distutils

RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python3 get-pip.py

RUN pip --version

RUN apt-get install libssl-dev

# download watchman
RUN wget https://github.com/facebook/watchman/releases/download/v2022.12.12.00/watchman_ubuntu20.04_v2022.12.12.00.deb
# RUN dpkg -i watchman_ubuntu20.04_v2022.12.12.00.deb
# RUN apt-get -f -y install
# RUN watchman version

#install pyre
RUN git clone https://github.com/facebook/pyre-check.git && \
cd pyre-check/stubs/typeshed/ && \
unzip typeshed.zip && cd ../../..

RUN pip install --upgrade pip
RUN pip install setuptools-rust

# install libsa4py
RUN git clone https://github.com/saltudelft/libsa4py.git
RUN pip install -r libsa4py/requirements.txt
RUN pip install libsa4py/


RUN python3 -c "import nltk; nltk.download('stopwords')"
RUN python3 -c "import nltk; nltk.download('wordnet')"
RUN python3 -c "import nltk; nltk.download('omw-1.4')"
RUN python3 -c "import nltk; nltk.download('averaged_perceptron_tagger')"
