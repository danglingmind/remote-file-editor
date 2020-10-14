import logging
import os
import shutil
import socket
import threading
import time
from collections import deque

import select


class Queue:
    def __init__(self, maxsize=0):
        self.maxsize = maxsize
        self._init(maxsize)

        self.mutex = threading.Lock()

        self.not_empty = threading.Condition(self.mutex)

        self.not_full = threading.Condition(self.mutex)

        self.all_tasks_done = threading.Condition(self.mutex)
        self.unfinished_tasks = 0

    def task_done(self):
        with self.all_tasks_done:
            unfinished = self.unfinished_tasks - 1
            if unfinished <= 0:
                if unfinished < 0:
                    raise ValueError('task_done() called too many times')
                self.all_tasks_done.notify_all()
            self.unfinished_tasks = unfinished

    def join(self):
        with self.all_tasks_done:
            unfinished = self.unfinished_tasks - 1
            if unfinished <= 0:
                if unfinished < 0:
                    raise ValueError('task_done() called too many times')
                self.all_tasks_done.notify_all()
            self.unfinished_tasks = unfinished

    def join(self):
        with self.all_tasks_done:
            while self.unfinished_tasks:
                self.all_tasks_done.wait()

    def qsize(self):
        with self.mutex:
            return self._qsize()

    def empty(self):
        with self.mutex:
            return not self._qsize()

    def full(self):
        with self.mutex:
            return 0 < self.maxsize <= self._qsize()

    def put(self, item, block=True, timeout=None):
        with self.not_full:
            if self.maxsize > 0:
                if not block:
                    if self._qsize() >= self.maxsize:
                        raise Full
                elif timeout is None:
                    while self._qsize() >= self.maxsize:
                        self.not_full.wait()
                elif timeout < 0:
                    raise ValueError("'timeout' must be a non-negative number")
                else:
                    endtime = time() + timeout
                    while self._qsize() >= self.maxsize:
                        remaining = endtime - time()
                        if remaining <= 0.0:
                            raise Full
                        self.not_full.wait(remaining)
            self._put(item)
            self.unfinished_tasks += 1
            self.not_empty.notify()

    def get(self, block=True, timeout=None):
        with self.not_empty:
            if not block:
                if not self._qsize():
                    raise Empty
            elif timeout is None:
                while not self._qsize():
                    self.not_empty.wait()
            elif timeout < 0:
                raise ValueError("'timeout' must be a non-negative number")
            else:
                endtime = time() + timeout
                while not self._qsize():
                    remaining = endtime - time()
                    if remaining <= 0.0:
                        raise Empty
                    self.not_empty.wait(remaining)
            item = self._get()
            self.not_full.notify()
            return item

    def put_nowait(self, item):
        return self.put(item, block=False)

    def get_nowait(self):
        return self.get(block=False)

    def _init(self, maxsize):
        self.queue = deque()

    def _qsize(self):
        return len(self.queue)

    # Put a new item in the queue
    def _put(self, item):
        self.queue.append(item)

    # Get an item from the queue
    def _get(self):
        return self.queue.popleft()


def host2hostFileRecv(client_sock, files2sendQ):
    separator = '<SEPARATOR>'
    BUFFER_SIZE = 1024

    try:
        client_sock.send("READY".encode())
        # receive the file_name, file_path and file_size separated by <separator>
        rec_data = client_sock.recv(BUFFER_SIZE).decode().strip()
        client_sock.send("DONE".encode())

        file_name, file_path, file_size = rec_data.split(separator)
        file_name = file_name.strip()
        file_path = file_path.strip()
        # read the file
        f = open(file_path, 'r')
        file_content = f.read()

        # put the file and its meta_data into queue
        files2sendQ.put((rec_data, file_content))

        f.close()

        logging.info('File: ' + file_name + ' is ready to send ')
        client_sock.close()
    except:
        print('File Meta Not recieved properly')
        print('File-Meta: ' + rec_data)


def local2hostFileRecv(client_sock):
    separator = '<SEPARATOR>'
    buffer_size = 1024

    # Always receive the file from local
    try:
        while True:
            # receive meta data of the file
            rec_data = client_sock.recv(buffer_size).decode().strip()
            if rec_data == '':
                continue
            file_name, file_path, file_size = rec_data.split(separator)

            # send ACK for meta data
            client_sock.send('ACK_META'.encode())
            # process meta data
            file_name = file_name.strip()
            file_path = file_path.strip()
            file_size = int(file_size.strip())

            # temp file which will be copied to the original locations
            if not os.path.exists('.fromLocal'):
                os.mkdir(os.path.abspath('.fromLocal'))

            temp_file_path = '.fromLocal/' + file_name

            f = open(temp_file_path, 'wb')
            total_bytes_read = 0
            while total_bytes_read < file_size:
                bytes_read = client_sock.recv(buffer_size)
                total_bytes_read += len(bytes_read)
                if not bytes_read:
                    # close the file
                    f.close()
                    # file transmission is done
                    break
                # write the file
                f.write(bytes_read)
            f.close()
            logging.info('File name : ' + file_name + ', Recieved from remote')

            # copy the temp file to the original file_path
            try:
                shutil.copy(temp_file_path, file_path)
                # send success msg to remote
                client_sock.send('SAVED'.encode())

                logging.info('File : ' + file_name + ' Saved Successfully')

                # remove the file from temp
                os.remove(temp_file_path)

            except Exception as e:
                logging.error('Unable to copy ' + file_name + ' | Error: ' +
                              str(e))
                # send the error back to remote
                client_sock.send(str(e).encode())
    except socket.error as e:
        logging.error('Error in receiving file from remote: ' + str(e))
        client_sock.close()


def host2localFileSendWorker(client_sock, files2sendQ):
    buffer_size = 1024
    try:
        while not files2sendQ.empty():
            # send start signal
            client_sock.send('START'.encode())
            # get the item from queue
            item = files2sendQ.get()

            # check the socket
            read_sock, send_sock, errored = select.select([client_sock],
                                                          [client_sock], [], 5)
            if len(errored) > 0:
                client_sock.shutdown()
                raise socket.error('client socket closed')

            # receive ready signal
            _ = client_sock.recv(buffer_size).decode()

            file_meta, file_content = item
            print(file_meta)
            # send file's meta data
            client_sock.send(file_meta.encode())
            print("sent")
            # wait for client's ACK for metadata
            _ = client_sock.recv(buffer_size)

            # send the file
            client_sock.sendall(file_content.encode())

            files2sendQ.task_done()

            logging.info('File sent to remote.')

            # ack for file
            _ = client_sock.recv(buffer_size).decode()

        # close the socket
        client_sock.close()

    except socket.error as e:
        logging.error('Could not connect to client : ' + str(e))
        # push item back to the queue
        files2sendQ.put(item)
        files2sendQ.task_done()
        client_sock.close()


''' Listeners '''


def host2hostListener(sock, q):
    sock.listen(10)
    threads = []
    while True:
        try:
            (cl_sock, (ip, port)) = sock.accept()
            # start a new thread
            x = threading.Thread(target=host2hostFileRecv, args=(cl_sock, q))
            threads.append(x)
            x.start()
        except KeyboardInterrupt as e:
            logging.error('Caught KeyboardInterrupt , Exiting !!!')

    # wait for all the threads
    for th in threads:
        th.join()


def host2localListener(sock, q):
    sock.listen(1)
    threads = []
    while True:
        try:
            (cl_sock, (ip, port)) = sock.accept()
            # start a new thread
            x = threading.Thread(target=host2localFileSendWorker,
                                 args=(cl_sock, q))
            threads.append(x)
            x.start()
        except KeyboardInterrupt as e:
            logging.error('Caught KeyboardInterrupt , Exiting !!!')

    # wait for all the threads
    for th in threads:
        th.join()


def local2hostListener(sock, q):
    sock.listen(10)
    threads = []
    while True:
        try:
            (cl_sock, (ip, port)) = sock.accept()
            # start a new thread
            x = threading.Thread(target=local2hostFileRecv, args=[cl_sock])
            threads.append(x)
            x.start()
        except KeyboardInterrupt as e:
            logging.error('Caught KeyboardInterrupt , Exiting !!!')

    # wait for all the threads
    for th in threads:
        th.join()


if __name__ == '__main__':
    # configure logs
    logging.basicConfig(
        filename='.host_process.log',
        format=
        '%(asctime)s.%(msecs)03d %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
        datefmt='%Y-%m-%d,%H:%M:%S',
        level=logging.DEBUG)

    logging.info('Remote Edit Service started')

    # TCP_IP = '0.0.0.0'
    TCP_IP = socket.gethostname()

    # Queue for the files and send it to remote one by one
    files2sendQ = Queue()
    ''' HOST --> HOST '''
    host2host_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host2host_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    host2host_sock.bind((TCP_IP, 5003))
    th1 = threading.Thread(target=host2hostListener,
                           args=(host2host_sock, files2sendQ))
    th1.start()
    ''' HOST --> REMOTE '''
    host2local_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host2local_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    host2local_sock.bind((TCP_IP, 5001))
    th3 = threading.Thread(target=host2localListener,
                           args=(host2local_sock, files2sendQ))
    th3.start()
    ''' REMOTE --> HOST (multithread) '''
    local2host_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local2host_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    local2host_sock.bind((TCP_IP, 5002))
    th2 = threading.Thread(target=local2hostListener,
                           args=(local2host_sock, files2sendQ))
    th2.start()

    th1.join()
    th2.join()
    th3.join()
