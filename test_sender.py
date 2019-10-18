import multiprocessing
import time
from unittest import TestCase, mock

from files_sender import Uploader


def mock_file_sender(path_to_file, ):
    """
    Simulator of the loading process

    :param path_to_file: string
    :return: (path_to_file, status code, status name)
    """

    time.sleep(.6)
    if '7' in path_to_file:
        result = path_to_file, 403, 'Forbidden'
    elif '9' in path_to_file:
        result = path_to_file, 404, 'Not Found'
    else:
        result = path_to_file, 200, 'OK'
    print(f'{multiprocessing.current_process().name} -> {result}')
    return result


class TestUploader(TestCase):

    def test_file_not_found(self):
        uploader = Uploader([], 2, None)
        result = uploader.file_sender('3.txt')
        expect = ('3.txt', 404, 'File not found')
        self.assertEqual(result, expect)

    def test_send_file(self):
        uploader = Uploader([], 2, None)
        with mock.patch('requests.post'):
            file, status_code, reason = uploader.file_sender('requirements.txt')
            self.assertEqual(file, 'requirements.txt')

    def test_start(self):
        test_files_list = [f'{i}.txt' for i in range(7)]
        m = multiprocessing.Manager()
        q = m.Queue()

        uploader = Uploader(test_files_list, 2, q)
        uploader.start()

        expect_errors = {'0.txt': 404, '1.txt': 404, '2.txt': 404, '3.txt': 404,
                         '4.txt': 404, '5.txt': 404, '6.txt': 404}
        self.assertEqual(uploader.errors, expect_errors)

        q_result = []
        while uploader.is_active():
            q_result.append(q.get())
        self.assertEqual(len(q_result), 7)
