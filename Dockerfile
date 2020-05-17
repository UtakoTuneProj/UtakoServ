FROM python:3.6-buster
LABEL MAINTAINER="nanamachi<7machi@nanamachi.net>"

RUN mkdir /UtakoServ
RUN apt-get update &&\
    apt-get install -y --no-install-recommends ffmpeg python3-tk &&\
    apt-get install -y --no-install-recommends gcc musl g++ gfortran libpng-dev
RUN pip3 install pipenv
COPY  ./Pipfile ./Pipfile.lock /UtakoServ/
WORKDIR /UtakoServ
RUN pipenv sync

COPY ./ /UtakoServ/

ENTRYPOINT ["pipenv", "run", "gunicorn"]
CMD ["-c", "conf/gunicorn.conf.py", "bin.flask_entrypoint:app"]
ENV PYTHON_ENV=development