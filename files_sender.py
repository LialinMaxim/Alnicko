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

    def __init__(self, files, num_process=None, queue=None, ):
        self.files_list = files
        self.num_process = num_process or multiprocessing.cpu_count() * 2
        self.queue = queue
        self.errors = {}
        self.done = 0
        self._complete = 0
        self._star_time = None
        self._end_time = None

    def __str__(self):

        return f'\n' \
            f'< Uploader obj -  ' \
            f'files: {len(self.files_list)}, ' \
            f'done: {self.done}, ' \
            f'errors: {len(self.errors)}, ' \
            f'loading time: {self.get_loading_time()} sec >\n'

    def start(self):
        self._star_time = datetime.datetime.utcnow()
        with multiprocessing.Pool(processes=3) as pool:
            for p in pool.imap_unordered(self.test_file_sender, self.files_list):
                result, process = p
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
                self._print_progress(process, result)
        self._end_time = datetime.datetime.utcnow()

    # testing worker
    @staticmethod
    def test_file_sender(path_to_file):
        """
        Simulator of the loading process

        :param path_to_file: string
        :return: (path_to_file, status code, status name)
        """

        time.sleep(.4)

        if '7' in path_to_file:
            result = path_to_file, 403, 'Forbidden'
        elif '9' in path_to_file:
            result = path_to_file, 404, 'Not Found'
        else:
            result = path_to_file, 200, 'OK'

        return result, multiprocessing.current_process().name

    # worker example
    def file_sender(self, path_to_file):

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

    def _print_progress(self, current_process, output):
        progress = self._complete / len(self.files_list)
        print(
            f'{current_process}_result: {output} \n'
            f'Progress: {int(progress * 100)}% \n'
        )


if __name__ == '__main__':
    test_files_list = [f'{i}.txt' for i in range(34)]
    m = multiprocessing.Manager()
    q = m.Queue()

    uploader = Uploader(test_files_list, 3, q)
    uploader.start()

    # Start printing results
    while uploader.is_active():
        print('Result:', q.get())

    print(uploader)
    print('loading errors:', uploader.errors)
    print('loading time:', uploader.get_loading_time(), 'seconds')
