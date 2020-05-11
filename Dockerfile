FROM python:3.6-buster
MAINTAINER nanamachi

RUN apt-get update &&\
    apt-get install -y --no-install-recommends ffmpeg python3-tk &&\
    apt-get install -y --no-install-recommends gcc musl g++ gfortran libpng-dev
COPY  ./dependencies.dat /
RUN pip3 install -U pip &&\
    pip install -r /dependencies.dat
COPY ./ /UtakoServ/

WORKDIR /UtakoServ
ENTRYPOINT ["gunicorn"]
CMD ["-c", "conf/gunicorn.conf.py", "bin.flask_entrypoint:app"]
ENV PYTHON_ENV=development