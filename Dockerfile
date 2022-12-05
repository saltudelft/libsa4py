FROM --platform=linux/amd64 ubuntu 

# VOLUME [ "/data/source", "/data/results" ]

# define watchmen version for watchman installation
ARG WM_VERSION=v2022.11.07.00

RUN ln -snf /usr/share/zoneinfo/$CONTAINER_TIMEZONE /etc/localtime && echo $CONTAINER_TIMEZONE > /etc/timezone

RUN apt-get update

# install packages needed
RUN apt-get install vim
RUN apt-get install -y wget
RUN apt-get install unzip
RUN apt-get install -y git 
RUN apt install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get install -y python3.9
RUN apt-get install -y python3-pip
RUN apt install -y  expect

RUN wget http://debian.mirror.ac.za/debian/pool/main/o/openssl/libssl1.1_1.1.1o-1_amd64.deb
RUN dpkg -i libssl1.1_1.1.1o-1_amd64.deb

# install watchman
RUN wget https://github.com/facebook/watchman/releases/download/$WM_VERSION/watchman-$WM_VERSION-linux.zip && \
unzip watchman-$WM_VERSION-linux.zip && \
cd watchman-$WM_VERSION-linux && \
mkdir -p /usr/local/{bin,lib} /usr/local/var/run/watchman && \
cp bin/* /usr/local/bin && \
cp lib/* /usr/local/lib && \
chmod 755 /usr/local/bin/watchman && \
chmod 2777 /usr/local/var/run/watchman && \
cd .. && \
rm -fr watchman-$WM_VERSION-linux.zip watchman-$WM_VERSION-linux

#install pyre
RUN git clone https://github.com/facebook/pyre-check.git && \
cd pyre-check/stubs/typeshed/ && \
unzip typeshed.zip && cd ../../..


# install libsa4py
RUN git clone https://github.com/LangFeng0912/libsa4py.git
RUN pip install -e libsa4py/
RUN pip install -r libsa4py/requirements.txt

RUN python3 -c "import nltk; nltk.download('stopwords')"
RUN python3 -c "import nltk; nltk.download('wordnet')"
RUN python3 -c "import nltk; nltk.download('omw-1.4')"
RUN python3 -c "import nltk; nltk.download('averaged_perceptron_tagger')"
