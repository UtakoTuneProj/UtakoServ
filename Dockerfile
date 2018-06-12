FROM python:3.5-jessie
MAINTAINER nanamachi

RUN echo 'http://ftp.uk.debian.org/debian jessie-backports main' >> /etc/apt/source.list &&\
    apt-get update &&\
    apt-get install -y --no-install-recommends ffmpeg python3-tk &&\
    apt-get install -y --no-install-recommends gcc musl g++ gfortran libpng-dev
COPY  ./dependencies.dat /
RUN pip3 install -U pip &&\
    pip install -r /dependencies.dat
COPY ./ /UtakoServ/
