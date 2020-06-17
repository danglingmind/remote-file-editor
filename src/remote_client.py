#!/usr/local/bin/python3
""" remote side client process """
import configparser
import os
import socket
import subprocess as sp
import sys
import threading
import time
import logging
from platform import system


class NewHostConnection:
    def __init__(self, ip, port):
        self.host_ip = ip
        self.port = port
        self.__host_sock = None
        self.__connection_time = time.time()
        self.__refresh_flag = False

    @property
    def host_sock(self):
        return self.__host_sock

    @property
    def connection_time(self):
        return self.__connection_time

    @property
    def refresh_flag(self):
        return self.__refresh_flag

    @refresh_flag.setter
    def refresh_flag(self, value):
        self.__refresh_flag = value

    @connection_time.setter
    def connection_time(self, value):
        self.__connection_time = value

    @host_sock.setter
    def host_sock(self, value):
        self.__host_sock = value

    def connect_to_host(self):
        try:
            new_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            new_sock.connect((self.__host_sock, self.port))
            self.__connection_time = time.time()
            self.__host_sock = new_sock
        except socket.error as e:
            print('Error: '+str(e))

    def reconnect(self):
        try:
            # create a new connection before closing the existing one
            new_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            new_sock.connect((self.__host_sock, self.port))
            # close existing socket
            self.__host_sock.close()
            # set the new one
            self.__host_sock = new_sock
            # change connection_time
            self.__connection_time = time.time()
        except socket.error as e:
            print('Error: '+str(e))

    def _refresh_daemon(self, interval: int):
        while self.__refresh_flag:
            # after interval time reconnect, which will basically refresh the socket
            time.sleep(3)
            if time.time() - self.__connection_time > interval:
                self.reconnect()

    def refresh(self, interval: int):
        self.__refresh_flag = True
        # initiate a daemon which will refresh the connection after the interval which is provided
        th = threading.Thread(target=self._refresh_daemon(), daemon=True, args=[interval])
        th.start()

    def stop_refresh(self):
        self.__refresh_flag = False

    def close(self):
        self.__host_sock.close()


class Config:
    def __init__(self, filepath):
        self.filepath = filepath
        self.editor_mac = ''
        self.editor_windows = ''
        self.host_address = ''
        self.platform = system()
        self.config = configparser.ConfigParser()

        # if file exists then read all the values
        if os.path.exists(self.filepath):
            self.config.read(self.filepath)

            address = self.config['host']['address']
            if len(address) == 0:
                hIp = input('Enter host IP : ')
                self.config['host']['address'] = hIp.strip()

            editor = self.config['editor'][self.platform]
            if len(editor) == 0:
                ed = input('Enter editor path : ').strip()
                self.config['editor'][self.platform] = ed

        else:
            # if file is not present
            # create the file
            self.config.add_section('host')
            address = input('Enter the host address :').strip()
            self.config['host']['address'] = address
            self.host_address = address

            self.config.add_section('editor')
            if self.platform == 'Darwin':
                ed = input('Enter Exact Same Name of the editor as shown in Applications : ').strip()
                self.editor_mac = ed
            elif self.platform == 'Windows':
                ed = input('Enter editor\'s Executable path : ').strip()
                self.editor_windows = ed

            self.config['editor'][self.platform] = ed

        # write/update the config file with values
        with open(self.filepath, 'w') as configfile:
            self.config.write(configfile)

    def update_config(self):
        print("Host Address : "+str(self.host_address))
        if self.platform == 'Windows':
            print("Editor : "+str(self.editor_windows))
        else:
            print("Editor : "+str(self.editor_mac))

        want = input('Want to modify ? Y/N :\n').strip()
        if want.lower() == 'y':
            ch = input('Change host address Y/N').strip()
            if ch.lower() == 'y':
                self.host_address = input('New Address : ').strip()
                self.config['host']['address'] = self.host_address
            ch = input('Change Editor Y/N').strip()
            if ch.lower() == 'y':
                if self.platform == 'Windows':
                    self.editor_windows = input('New Editor : ').strip()
                    self.config['editor'][self.platform] = self.editor_windows
                else:
                    self.editor_mac = input('New Editor : ').strip()
                    self.config['editor'][self.platform] = self.editor_mac

        # write into the confi file
        with open(self.filepath, 'w') as configfile:
            self.config.write(configfile)


class DirWatcher:
    def __init__(self, path: str):
        self.__dir_path = path
        self.__watch = False

    @property
    def watch(self):
        return self.__watch

    @watch.setter
    def watch(self, value):
        self.__watch = value

    def __send_file(self, filename):
        # create a connection to host

        # send the file
        pass    #

    def __watch_daemon(self):
        while self.__watch:
            time.sleep(1)
            # check for any files to get change inside the directory provided
            # file list
            files = [f for _, _, f in os.walk(self.__dir_path)][0]
            for fl in files:
                pass
            #TODO: implement files last modified record meta data

    def start_watch(self):
        self.__watch = True
        th = threading.Thread(target=self.__watch_daemon, daemon=True, args=[])
        th.start()

    def stop_watch(self):
        self.__watch = False


class FileRecord:
    def __init__(self):
        self.db = {}

    def add_file(self, filename: str, filepath: str, last_mod_time: time.time()):
        self.db[filename] = (filepath, last_mod_time)

    def get_file(self, filename):
        if filename in self.db:
            return self.db[filename]
        else:
            return None

    def update_file(self, filename: str, mod_time: time.time()):
        if filename in self.db:
            self.db[filename][1] = mod_time
        else:
            return None


#TODO : Dir Watcher class  : watcher will initiate a thread to send the file back to server
#TODO : open file function
#TODO : custom logging class
#TODO : add authentication on startup (use init for authenticaion)(try to incorporate SSH key as auth)

def configSetup():
    config = configparser.ConfigParser()
    hostIp = ''
    editor = ''
    # check the file
    if not os.path.exists(r'host_config.ini'):
        # create the file
        config.add_section('host')
        address = input('Enter the host address :').strip()
        config['host']['address'] = address
        hostIp = address

        config.add_section('editor')
        if platform.system() == 'Darwin':
            ed = input('Enter Exact Same Name of the editor as shown in Applications : ').strip()
        elif platform.system() == 'Windows':
            ed = input('Enter editor\'s Executable path : ').strip()

        config['editor'][platform.system()] = ed
        editor = ed

        with open(r'host_config.ini', 'w') as configfile:
            config.write(configfile)
    else:
        config.read(r'host_config.ini')

        # read host address
        hostIp = config['host']['address']
        if len(hostIp) == 0:
            hIp = input('Enter host IP : ')
            config['host']['address'] = hIp.strip()
            hostIp = hIp
        else:
            print(f'Host : {hostIp}')

        # read the editor
        editor = config['editor'][platform.system()]
        if editor == '':
            ed = input('Enter editor path : ').strip()
            config['editor'][platform.system()] = ed
            editor = ed
        else:
            print(f'Editor : {editor}')
            print('Change the values in host_config.ini to use other host/editor!!')

        # write all the first inputs into the file
        with open(r'host_config.ini', 'w') as configfile:
            config.write(configfile)

    return hostIp, editor


def fileWatcher1(host_ip, files_rec, dir_path):
    host_send_port = 5002

    # monitor the change in the file
    while True:
        time.sleep(1)

        files = [f for _, _, f in os.walk(dir_path)][0]

        for file_name in files:

            file_path_on_local = f'{dir_path}/{file_name}'

            current_mod_time = os.path.getmtime(file_path_on_local)

            if file_name in files_rec:

                file_path, file_init_time = files_rec[file_name]

                # if file is modified
                if current_mod_time > file_init_time:
                    files_rec[file_name] = (file_path, current_mod_time)

                    try:
                        # connect to host to send the file
                        host_send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        host_send_sock.connect((host_ip, host_send_port))
                        logging.info('Connected to host')

                        # read the modified file
                        fl = open(file_path_on_local, 'r')
                        file_content = fl.read()

                        # send the Metadata
                        filemeta = f'{file_name}{separator}{file_path}{separator}{len(file_content)}'
                        host_send_sock.send(filemeta.encode())

                        # receive ACK from host
                        _ = host_send_sock.recv(buffer_size).decode()

                        # send the file
                        host_send_sock.sendall(file_content.encode())
                        logging.info(f'File : {file_name} Sent')
                        # close file
                        fl.close()

                        # ack for sent file
                        file_ack = host_send_sock.recv(buffer_size).decode()
                        if file_ack == 'SAVED':
                            logging.info(f'File : {file_name} Saved successfully!!')
                        else:
                            print(f'[+] Error while saving the file : {file_ack}\n [+][+] Resolve the issue and save it again to resend')
                            logging.error(f'Error while saving the file : {file_ack}')
                    except (socket.error, KeyboardInterrupt) as e:
                        print(f'[+] Error when sending file : {e}')
                        logging.error(f'Error when sending file : {e}')
                        host_send_sock.close()
                        # close the file if still open
                        try:
                            fl.close()
                        except Exception:
                            pass
                        # come out of the loop
                        break


def fileWatcher2(host_ip, file_name, file_path, files_rec, file_path_on_local):

    host_send_port = 5002

    # connect to host to send the file
    host_send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_send_sock.connect((host_ip, host_send_port))

    # last modification time of the file
    last_modified = os.path.getmtime(file_path_on_local)

    # monitor the change in the file
    while True:
        time.sleep(1)

        modifed_time = os.path.getmtime(file_path_on_local)

        # if changed then
        if modifed_time > last_modified:
            last_modified = modifed_time
            try:
                # read the modified file
                fl = open(file_path_on_local, 'r')
                file_content = fl.read()

                # send the Metadata
                filemeta = f'{file_name}{separator}{file_path}{separator}{len(file_content)}'
                host_send_sock.send(filemeta.encode())

                # receive ACK from host
                _ = host_send_sock.recv(buffer_size).decode()

                # send the file
                host_send_sock.sendall(file_content.encode())

                # close file
                fl.close()

                # ack for sent file
                file_ack = host_send_sock.recv(buffer_size).decode()
                if file_ack == 'SAVED':
                    print('[+] File saved successfully!!')
                else:
                    print(f'[+] Error while saving the file : {file_ack}\n [+][+] Resolve the issue and save it again to resend')
            except (socket.error, KeyboardInterrupt) as e:
                print(f'[+] Error when sending file : {e}')
                host_send_sock.close()
                # close the file if still open
                try:
                    fl.close()
                except Exception:
                    pass
                # come out of the loop
                break
    print(f'[+] Filewatcher closed for {file_name}')


def openFile(filepath, default_editor):
    try:
        if platform.system() == 'Windows':
            sp.Popen([default_editor, filepath])
        elif platform.system() == 'Darwin':
            os.system(f'open -a \'{default_editor}\' {filepath}')
    except Exception as e:
        print(f'[!] Could not open the file {e}')
        logging.error(f'Could not open the file {e}')


if __name__ == '__main__':

    logging.basicConfig(filename='.remote_client.log', filemode='a', format='%(asctime)s.%(msecs)03d %(levelname)s {%(module)s} [%(funcName)s] %(message)s', datefmt='%Y-%m-%d,%H:%M:%S', level=logging.DEBUG)
    logging.info('Started')
    # host and editor details
    host_ip, default_editor = configSetup()

    buffer_size = 1024
    separator = '<SEPARATOR>'
    # default_editor = r'C:/Program Files/Sublime Text 3/subl.exe'

    # Received files data
    # {file_name : ('path on host', 'initial time of save')}
    files_rec = {}

    # save the received files into local_temp dir
    local_temp_dir = r'.local_temp'
    # check if the dir is present if not then create
    if not os.path.exists(local_temp_dir):
        logging.info(f'Created temp folder : {local_temp_dir}')
        os.mkdir(os.path.abspath(local_temp_dir))

    # clean the temp before receiving files
    files = [f for root, _, f in os.walk(local_temp_dir, topdown=False)][0]
    for name in files:
        os.remove(f'{local_temp_dir}/{name}')

    # start a watcher on the temp dir
    x = threading.Thread(target=fileWatcher1, daemon=True, args=(host_ip, files_rec, local_temp_dir))
    x.start()

    host_recv_port = 5001

    try:
        # connect to the host to receive file
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host_ip, host_recv_port))
        logging.info('connected to host to receive file')
    except socket.error as e:
        logging.error(f'Host is down : {e}')
        print(f'[!] Host is down : {e}')
        print('[x] Could not connect to host, BYE !!!')
        time.sleep(3)
        sys.exit(1)

    # Always accept files from host
    while True:
        try:
            sock.send('READY'.encode())

            # receive file's META first
            recv_meta_data = sock.recv(buffer_size).decode().strip()
            if recv_meta_data == '':
                continue
            # process metadata
            file_name, file_path, file_size = recv_meta_data.split(separator)

            # Send ACK to host to send file
            sock.send('META_ACK'.encode())

            file_name = file_name.strip()
            file_path = file_path.strip()
            file_size = int(file_size.strip())

            # Start receiving the file
            temp_file = f'{local_temp_dir}/{file_name}'
            # save the file into local temp dir
            f = open(temp_file, 'wb')
            total_bytes_read = 0
            while total_bytes_read < file_size:
                bytes_read = sock.recv(buffer_size)
                total_bytes_read += len(bytes_read)
                if not bytes_read:
                    # close the file
                    f.close()
                    # file transmission is done
                    break
                # write the file
                f.write(bytes_read)
            f.close()
            logging.info(f'Received File : {file_name}')

            # open file in default editor
            openFile(temp_file, default_editor)

            # wait for editor to start
            time.sleep(2)

            # record the file
            files_rec[file_name] = (file_path, os.path.getmtime(temp_file))

        except (socket.error, KeyboardInterrupt) as e:
            logging.error(f'Client got some error : {e}')
            print(f'[!] Client got some error : {e}')
            # close socket
            sock.close()
            # sys.exit(1)

            # give option to reconnect or exit
            while True:
                choice = input('Press Y to reconnect or N to exit : ').strip().upper()
                if choice == 'N':
                    sys.exit(0)
                elif choice == 'Y':
                    try:
                        # retry connecting
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.connect((host_ip, host_recv_port))
                        print(f'[+] Connected to host...')
                        logging.info('Connected to host')
                        break
                    except socket.error as err:
                        print(f'[!] Could not connect to host: {err}')
                        logging.error(f'Could not connect to host: {err}')
                        continue
                else:
                    continue
            # if comes here then you are connected again continue
            continue
