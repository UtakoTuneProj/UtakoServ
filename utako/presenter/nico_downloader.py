#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import subprocess as sbproc
import signal

from google.cloud import storage
import youtube_dl

from utako import root_logger
from utako.common_import import *
from utako.exception.restricted_movie_exception import RestrictedMovieException

class NicoDownloader:
    def __init__(self):
        client = storage.client.Client(config['gcp']['PROJECT_ID'])
        self.partial_file_bucket = client.get_bucket(config['gcp']['STORAGE_PARTIAL_BUCKET'])
        self.output_filename_template = 'tmp/mp4/%(id)s.mp4'

    def __call__(self, mvid, retries=1, force=False, dl_timeout_sec=60, use_partial=False): #ランキング取得・キュー生成部
        if use_partial:
            self._load_partial_file(mvid)
        self.downloader = youtube_dl.YoutubeDL({
            'outtmpl': self.output_filename_template,
            'retries': retries,
            'format': 'worstaudio/worst',
            'logger': root_logger,
            'noprogress': True,
        })

        def timeout_handler(signalnum, stackframe):
            raise TimeoutError
        signal.signal(signal.SIGALRM, timeout_handler)

        try:
            signal.alarm(dl_timeout_sec)
            self.downloader.download(['http://www.nicovideo.jp/watch/{}'.format(mvid)])

        except youtube_dl.utils.DownloadError as e:
            signal.alarm(0)
            if re.compile(
                "niconico reports error: (invalid_v[123]|domestic_video)"
            ).search(e.args[0]):
                raise RestrictedMovieException(mvid)
            elif retries < 1:
                raise e
            else:
                time.sleep(10)
                self(mvid, retries=retries - 1, dl_timeout_sec=dl_timeout_sec, force=force)

        except TimeoutError as e:
            signal.alarm(0)
            dl_process.terminate()
            root_logger.warning('Downloading Video {} has been timed out'.format(mvid))
            if use_partial:
                self._save_partial_file(mvid)
            raise e

        else:
            signal.alarm(0)
            process = sbproc.run([
                'ffmpeg',
                '-i', #infile
                'tmp/mp4/{}.mp4'.format(mvid),
                '-y' if force else '-n', #overwrite if force is True
                '-aq', #bitrate
                '128k',
                '-ac', #channels
                '1', #monoral
                '-ar', #sampling rate
                '44100',
                'tmp/wav/{}.wav'.format(mvid),#outfile name
            ], stderr=sbproc.PIPE)
            if process.returncode != 0: # if process does not stop accurately
                os.remove('tmp/mp4/{}.mp4'.format(mvid))
                root_logger.warning(process.stderr)
                time.sleep(10)
                self(mvid, retries=retries, dl_timeout_sec=dl_timeout_sec, force=force)

    def _save_partial_file(self, movie_id):
        src_path = Path(self.output_filename_template % { 'id': movie_id } + '.part')
        blob = self.partial_file_bucket.blob('partial_download_save/{}'.format(src_path.name))

        if not src_path.exists() or src_path.is_dir():
            return
        with open(src_path, 'rb') as f:
            blob.upload_from_file(f)
            root_logger.info('Partial Video {} has been saved'.format(movie_id))

    def _load_partial_file(self, movie_id):
        dst_path = Path(self.output_filename_template % { 'id': movie_id } + '.part')
        blob = self.partial_file_bucket.blob('partial_download_save/{}'.format(dst_path.name))

        if not blob.exists():
            return
        with open(dst_path, 'wb') as f:
            blob.download_to_file(f)
            root_logger.info('Partial Video {} has been downloaded'.format(movie_id))
