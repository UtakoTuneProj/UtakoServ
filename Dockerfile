FROM python:3.6-buster
LABEL MAINTAINER="nanamachi<7machi@nanamachi.net>"

RUN mkdir /UtakoServ
RUN apt-get update &&\
    apt-get install -y --no-install-recommends ffmpeg python3-tk libsndfile1 &&\
    apt-get install -y --no-install-recommends gcc musl g++ gfortran libpng-dev
RUN pip3 install pipenv
COPY  ./Pipfile ./Pipfile.lock ./.gitcookies /UtakoServ/
WORKDIR /UtakoServ
RUN git config --global http.cookiefile .gitcookies &&\
    pipenv install --system --deploy &&\
    rm -rf ~/.gitcookies

COPY ./ /UtakoServ/

ENTRYPOINT ["gunicorn"]
CMD ["-c", "conf/gunicorn.conf.py", "bin.flask_entrypoint:app"]
ENV PYTHON_ENV=development
ENV TZ=Asia/Tokyo
