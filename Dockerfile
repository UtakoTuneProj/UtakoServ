FROM python:3.5-stretch
MAINTAINER nanamachi

RUN apt-get update &&\
    apt-get install -y --no-install-recommends ffmpeg python3-tk &&\
    apt-get install -y --no-install-recommends gcc musl g++ gfortran libpng-dev
COPY  ./dependencies.dat /
RUN pip3 install -U pip &&\
    pip install -r /dependencies.dat
COPY ./ /UtakoServ/
