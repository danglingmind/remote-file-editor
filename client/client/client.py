#!/usr/local/bin/python3
""" remote side client process """
import configparser
import os
import queue
import socket
import subprocess as sp
import sys
import threading
import time
import tkinter
from platform import system
from tkinter import messagebox


class NewHostConnection:
    def __init__(self, ip, port):
        self.host_ip = ip
        self.port = port
        self.host_sock = socket.socket()
        self.connected = False
        self.__connection_time = time.time()
        self.__refresh_flag = False

    def connect_to_host(self):
        try:
            new_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            new_sock.connect((self.host_ip, self.port))
            self.__connection_time = time.time()
            self.host_sock = new_sock
            self.connected = True
        except socket.error as e:
            print('Error: ' + str(e))

    def reconnect(self):
        try:
            # create a new connection before closing the existing one
            new_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            new_sock.connect((self.host_ip, self.port))
            # close existing socket
            self.host_sock.close()
            # set the new one
            self.host_sock = new_sock
            # change connection_time
            self.__connection_time = time.time()
            self.connected = True
        except socket.error as e:
            self.connected = False
            print('Error: ' + str(e))

    def stop_refresh(self):
        self.__refresh_flag = False

    def close(self):
        self.connected = False
        self.host_sock.close()


class Config:
    file_path = ''
    editor_mac = ''
    editor_windows = ''
    host_address = ''
    buffer_size = 1024
    separator = '<SEPARATOR>'
    downstream_port = 5001
    upstream_port = 5002
    temp_dir = '.local_temp'
    platform = system()
    config = configparser.ConfigParser()

    @staticmethod
    def read_file(file_path):
        Config.file_path = file_path

        # if file exists then read all the values
        if os.path.exists(file_path):
            Config.config.read(file_path)

            # host address
            if len(Config.config['host']['address']) == 0:
                Config.host_address = input('Enter host IP : ').strip()
                Config.config['host']['address'] = Config.host_address
            else:
                Config.host_address = Config.config['host']['address']

            # editor
            if len(Config.config['editor'][Config.platform]) == 0:
                if Config.platform == 'Darwin':
                    Config.editor_mac = input('Enter Exact Same Name of the editor as shown in Applications : ').strip()
                    Config.config['editor'][Config.platform] = Config.editor_mac
                elif Config.platform == 'Windows':
                    Config.editor_windows = input('Enter editor\'s Executable path : ').strip()
                    Config.config['editor'][Config.platform] = Config.editor_windows
            else:
                if Config.platform == 'Darwin':
                    Config.editor_mac = Config.config['editor'][Config.platform]
                elif Config.platform == 'Windows':
                    Config.editor_windows = Config.config['editor'][Config.platform]

            # buffer_size
            if len(Config.config['client']['buffer_size']) == 0:
                Config.config['client']['buffer_size'] = str(Config.buffer_size)
            else:
                Config.buffer_size = int(Config.config['client']['buffer_size'])

            # separator
            if len(Config.config['client']['separator']) == 0:
                Config.config['client']['separator'] = Config.separator
            else:
                Config.separator = Config.config['client']['separator']

            # download port
            if len(Config.config['client']['downstream_port']) == 0:
                Config.config['client']['downstream_port'] = str(Config.downstream_port)
            else:
                Config.downstream_port = int(Config.config['client']['downstream_port'])

            # upload port
            if len(Config.config['client']['upstream_port']) == 0:
                Config.config['client']['upstream_port'] = str(Config.upstream_port)
            else:
                Config.upstream_port = int(Config.config['client']['upstream_port'])

            # temp directory
            if len(Config.config['client']['temp_dir']) == 0:
                Config.config['client']['temp_dir'] = Config.temp_dir
            else:
                Config.temp_dir = Config.config['client']['temp_dir']
        else:
            # if file is not present create the file

            Config.config.add_section('host')
            address = input('Enter the host address :').strip()
            Config.config['host']['address'] = address
            Config.host_address = address

            Config.config.add_section('editor')
            if Config.platform == 'Darwin':
                ed = input('Enter Exact Same Name of the editor as shown in Applications : ').strip()
                Config.editor_mac = ed
                Config.config['editor'][Config.platform] = ed
            elif Config.platform == 'Windows':
                ed = input('Enter editor\'s Executable path : ').strip()
                Config.editor_windows = ed
                Config.config['editor'][Config.platform] = ed

            Config.config.add_section('client')
            Config.config['client']['buffer_size'] = str(Config.buffer_size)
            Config.config['client']['separator'] = Config.separator
            Config.config['client']['downstream_port'] = str(Config.downstream_port)
            Config.config['client']['upstream_port'] = str(Config.upstream_port)
            Config.config['client']['temp_dir'] = Config.temp_dir

        # write/update the config file with values
        with open(Config.file_path, 'w') as configfile:
            Config.config.write(configfile)

    @staticmethod
    def update_config():
        print("Host Address : " + str(Config.host_address))
        if Config.platform == 'Windows':
            print("Editor : " + str(Config.editor_windows))
        else:
            print("Editor : " + str(Config.editor_mac))

        want = input('Want to modify ? Y/N :\n').strip()
        if want.lower() == 'y':
            ch = input('Change host address Y/N').strip()
            if ch.lower() == 'y':
                Config.host_address = input('New Address : ').strip()
                Config.config['host']['address'] = Config.host_address
            ch = input('Change Editor Y/N').strip()
            if ch.lower() == 'y':
                if Config.platform == 'Windows':
                    Config.editor_windows = input('New Editor : ').strip()
                    Config.config['editor'][Config.platform] = Config.editor_windows
                else:
                    Config.editor_mac = input('New Editor : ').strip()
                    Config.config['editor'][Config.platform] = Config.editor_mac

        # write into the config file
        with open(Config.file_path, 'w') as configfile:
            Config.config.write(configfile)


class MetadataDict:
    def __init__(self):
        self.db = {}

    def add_file(self, filename: str, filepath: str, filesize: int):
        self.db[filename] = (filepath, filesize)

    def get_data(self, filename):
        if filename in self.db:
            return self.db[filename]
        else:
            return None


class DirWatcher:
    def __init__(self, path: str):
        self.dir_path = path
        self.__file_mod_time_record = {}
        self.__watch = False

    def __watch_daemon(self, send_queue: queue.Queue):
        while self.__watch:
            time.sleep(1)
            # file list inside the dir
            fls = [f for _, _, f in os.walk(self.dir_path)][0]
            for fl in fls:
                file_path_local = f'{self.dir_path}/{fl}'
                if fl not in self.__file_mod_time_record:
                    # add file into the record
                    self.__file_mod_time_record[fl] = (file_path_local, os.path.getmtime(file_path_local))
                else:
                    # if file is present
                    file_local_path, file_last_mod_time = self.__file_mod_time_record[fl]
                    file_curr_mod_time = os.path.getmtime(file_path_local)
                    if file_curr_mod_time > file_last_mod_time:
                        self.__file_mod_time_record[fl] = file_local_path, file_curr_mod_time
                        # file is updated add it to send_queue
                        f = open(file_path_local, 'r')
                        f_content = f.read()
                        # add it to send_queue
                        send_queue.put(item=(fl, f_content))

    def start_watch(self, send_queue: queue.Queue):
        self.__watch = True
        th = threading.Thread(target=self.__watch_daemon, daemon=True, args=[send_queue])
        th.start()

    def stop_watch(self):
        self.__watch = False


def error_popup(title, popup):
    root = tkinter.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", 1)
    messagebox.showerror(title=title, message=popup)
    root.mainloop()


class SendWorker:
    def __init__(self, q: queue.Queue, metadata_dict: dict):
        self.q = q
        self.metadata_dict = metadata_dict
        self.worker_threads = []
        self.sending = False

    def __send_worker(self, send_queue: queue.Queue):
        # connect to the host on upstream port
        send_conn = NewHostConnection(Config.host_address, Config.upstream_port)
        send_conn.connect_to_host()

        while self.sending:
            file_name, file_content = send_queue.get()
            file_path, _ = self.metadata_dict[file_name]
            metadata = f'{file_name}{Config.separator}{file_path}{Config.separator}{len(file_content)}'
            try:
                send_conn.host_sock.sendall(metadata.encode())
                _ = send_conn.host_sock.recv(Config.buffer_size)
                send_conn.host_sock.sendall(file_content.encode())
                save_ack = send_conn.host_sock.recv(Config.buffer_size).decode()
                if save_ack == 'SAVED':
                    print(f'[+] {file_name} is saved')
                else:
                    error_popup('File Save Error !',
                                f'File Not Saved : {save_ack}\nResolve the issue on host and Save the file again.')
            except socket.error as e:
                for i in range(3):
                    time.sleep(2)
                    send_conn.reconnect()
                    if send_conn.connected:
                        break

                if not send_conn.connected:
                    print(f'[x] Error occurred in sending {file_name}: {e}')

                self.q.put((file_name, file_content))
            # done on queue item
            self.q.task_done()

    def start(self, worker_count: int):
        self.sending = True
        for i in range(worker_count):
            th = threading.Thread(target=self.__send_worker, args=[self.q])
            th.start()
            self.worker_threads.append(th)

    def stop(self):
        self.sending = False
        for th in self.worker_threads:
            th.join()


def open_file(file_path):
    try:
        if system() == 'Windows':
            sp.Popen([Config.editor_windows, file_path])
        elif system() == 'Darwin':
            os.system(f'open -a \'{Config.editor_mac}\' {file_path}')
    except Exception as e:
        if system() == 'Darwin':
            error_popup('File Open Error !', 'Check the Editor Name')
        elif system() == 'Windows':
            error_popup('File Open Error !', 'Check the Editor\'s exe path')


def authenticate():
    try:
        username = input('Enter User Name : ').strip()
        password = input('Enter Password : ').split()
        # TODO: Implement the logic
    except KeyboardInterrupt as e:
        print('Bye..')
        time.sleep(2)
        sys.exit(0)


def main():
    # setup/read configuration file
    Config.read_file('.remote_config.ini')

    # store meta data of received files
    metadata_store = MetadataDict()

    # modified files queue
    modified_files_queue = queue.Queue()

    # file sending worker
    send_worker = SendWorker(modified_files_queue, metadata_store.db)
    send_worker.start(4)

    # setup the temp dir
    if not os.path.exists(Config.temp_dir):
        os.mkdir(os.path.abspath(Config.temp_dir))

    # clean the temp dir before receiving new files
    files = [f for root, _, f in os.walk(Config.temp_dir, topdown=False)][0]
    for name in files:
        os.remove(f'{Config.temp_dir}/{name}')

    # create a watcher instance on temp dir
    watcher = DirWatcher(Config.temp_dir)

    # start the watch
    watcher.start_watch(modified_files_queue)

    # connect to host on downstream port
    down_conn = NewHostConnection(Config.host_address, Config.downstream_port)
    down_conn.connect_to_host()
    print(down_conn.connected)
    if not down_conn.connected:
        error_popup('Connection Error', 'Error could not connect to host Bye !!!')
        time.sleep(4)
        os._exit(0)
    else:
        # connected to host successfully
        while True:
            try:
                down_conn.host_sock.send('READY'.encode())

                # file's metadata
                meta_data = down_conn.host_sock.recv(Config.buffer_size).decode().strip()
                if len(meta_data) == 0:
                    continue

                # process metadata
                file_name, file_path, file_size = meta_data.split(Config.separator)
                file_name = file_name.strip()
                file_path = file_path.strip()
                file_size = int(file_size.strip())

                # ACK metadata
                down_conn.host_sock.send('META_ACK'.encode())

                # receive the file
                temp_file_path = f'{Config.temp_dir}/{file_name}'
                f = open(temp_file_path, 'wb')
                total_bytes_received = 0
                while total_bytes_received < file_size:
                    bytes_read = down_conn.host_sock.recv(Config.buffer_size)
                    total_bytes_received += len(bytes_read)
                    if not bytes_read:
                        f.close()
                        break
                    f.write(bytes_read)
                f.close()

                # open file into editor
                open_file(temp_file_path)

                # store the metadata
                metadata_store.add_file(file_name, file_path, file_size)
            except socket.error as e:
                print(e)
                down_conn.close()
                while True:
                    choice = input('Press Y to reconnect or N to exit : ').strip().upper()
                    if choice == 'N':
                        sys.exit(0)
                    elif choice == 'Y':
                        down_conn.reconnect()
                        if down_conn.connected:
                            break
                        else:
                            continue
                    else:
                        continue

                continue  # start receiving again


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Keyboard Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
