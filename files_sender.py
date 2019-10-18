"""
Write module to upload some files to the remote server.
Uploading should be done in parallel.
Python multiprocessing module should be used.
Real uploading is not part of this task, use some dummy function for emulate upload.

Input data:
- List of files to upload
- Maximum number of parallel uploading process
- Queue for passing progress to the caller

Output data:
- Uploading progress
- Final uploading report (uploaded files and not uploaded)
"""

import multiprocessing
import ntpath
import os
import time
import datetime

import requests


class Uploader:
    server_url = 'http://my_site.com/test'

    def __init__(self, files, num_process, queue, worker=None):
        self.files_list = files
        self.num_process = num_process
        self.queue = queue
        self.worker = worker or self.file_sender
        self.errors = {}
        self.done = 0
        self._complete = 0
        self._star_time = None
        self._end_time = None
        self._is_terminate = None

    def __str__(self):
        return f'< Uploader obj -  ' \
            f'files: {len(self.files_list)}, ' \
            f'done: {self.done}, ' \
            f'errors: {len(self.errors)}, ' \
            f'loading time: {self.get_loading_time()} sec >'

    def start(self):
        self._star_time = datetime.datetime.utcnow()
        self._is_terminate = False
        with multiprocessing.Pool(processes=self.num_process) as pool:
            for result in pool.imap_unordered(self.worker, self.files_list):
                f, status_code, status_name = result

                if status_code != 200:
                    self.errors[f] = status_code
                    self.queue.put({
                        'file': f,
                        'error': status_name
                    })
                else:
                    self.done += 1
                    self.queue.put({
                        'file': f,
                        'done': status_name
                    })
                self._complete += 1

                # interrupted all process
                if self._is_terminate:
                    pool.terminate()
                    self._end_time = datetime.datetime.utcnow()
                    return 'The pool was terminated'

        self._end_time = datetime.datetime.utcnow()

    def stop(self):
        self._is_terminate = True

    def file_sender(self, path_to_file):
        time.sleep(.3)
        if os.path.isfile(path_to_file):
            head_path, file_name = ntpath.split(path_to_file)
            with open(path_to_file, 'rb') as f:
                r = requests.post(self.server_url, files={file_name: f})
                return path_to_file, r.status_code, r.reason
        else:
            return path_to_file, 404, 'File not found'

    def is_active(self):
        return self.queue.empty() is False

    def get_loading_time(self):
        loading_time = 0
        if self._end_time:
            loading_time = (self._end_time - self._star_time).total_seconds()
        return loading_time


if __name__ == '__main__':
    """    Shows how it works.    """

    from test_sender import mock_file_sender

    test_files_list = [f'{i}.txt' for i in range(14)]

    m = multiprocessing.Manager()
    q = m.Queue()

    uploader = Uploader(test_files_list, 3, q, worker=mock_file_sender)
    uploader.start()

    print('\n---Lading complete---')
    while uploader.is_active():
        print('Result:', q.get())

    print('\n', uploader)
    print('loading errors:', uploader.errors)
    print('loading time:', uploader.get_loading_time(), 'seconds')
