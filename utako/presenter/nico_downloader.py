#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import subprocess as sbproc
import signal
from pathlib import Path

from google.cloud import storage
import yt_dlp

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
        self.downloader = yt_dlp.YoutubeDL({
            'outtmpl': self.output_filename_template,
            'retries': retries,
            'format': 'worstaudio/worst',
            'logger': root_logger,
            'noprogress': True,
        })

        def timeout_handler():
            raise TimeoutError
        signal.signal(signal.SIGALRM, timeout_handler)

        download_target_path = Path(self.output_filename_template % { 'id': mvid })

        try:
            signal.alarm(dl_timeout_sec)
            self.downloader.download(['http://www.nicovideo.jp/watch/{}'.format(mvid)])
            if not download_target_path.is_file():
                raise TimeoutError

        except yt_dlp.utils.DownloadError as e:
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
            root_logger.warning('Downloading Video {} has been timed out'.format(mvid))
            if use_partial:
                self._save_partial_file(mvid)
            raise e

        else:
            signal.alarm(0)
            root_logger.info('Formatting Video {} '.format(mvid))
            process = sbproc.run([
                'ffmpeg',
                '-i', #infile
                download_target_path.as_posix(),
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
                download_target_path.unlink(missing_ok=True)
                root_logger.warning(process.stderr)
                time.sleep(10)
                self(mvid, retries=retries, dl_timeout_sec=dl_timeout_sec, force=force)
            root_logger.info('Formatted Video {} '.format(mvid))

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
