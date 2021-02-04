#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from multiprocessing import Process, Pipe
from queue import Empty
import subprocess as sbproc

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
        pipe_receiver, pipe_sender = Pipe()
        dl_process = self._create_download_process(pipe_sender, mvid)

        try:
            dl_process.start()

            for t in range(dl_timeout_sec):
                if pipe_receiver.poll(1):
                    result = pipe_receiver.recv()
                    root_logger.debug(result)
                    break
            else:
                dl_process.terminate()
                raise TimeoutError

            if not result['success']:
                raise result['error']['type'](*result['error']['args'])

        except youtube_dl.utils.DownloadError as e:
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
            dl_process.terminate()
            root_logger.warning('Downloading Video {} has been timed out'.format(mvid))
            if use_partial:
                self._save_partial_file(mvid)
            raise e

        else:
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

    def _create_download_process(self, pipe, movie_id):
        def wrapper(pipe, movie_id):
            try:
                self.downloader.download(['http://www.nicovideo.jp/watch/{}'.format(movie_id)])
            except Exception as e:
                pipe.send({
                    'success': False,
                    'error': {
                        'type': type(e),
                        'args': e.args
                    }
                })
            else:
                pipe.send({'success': True})

        return Process(
            target=wrapper,
            args=(pipe, movie_id)
        )

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
