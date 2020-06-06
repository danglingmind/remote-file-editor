#!/usr/local/bin/python3

import socket
import threading
import subprocess as sp
import time
import os
import sys


def fileWatcher2(file_name, file_path, file_size, file_path_on_local):

    # connect to the host
    host_ip = '0.0.0.0'
    host_send_port = 5002

    # connect to host to send the file
    host_send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_send_sock.connect((host_ip, host_send_port))
    print('[+] Connected to host to send files...')

    # last modification time of the file
    last_modified = os.path.getmtime(file_path_on_local)
    print(f'[----] {file_name} Initial mod time: {last_modified}')
    # monitor the change in the file
    while True:
        time.sleep(1)

        modifed_time = os.path.getmtime(file_path_on_local)

        # if changed then
        if modifed_time > last_modified:
            print(f'[+] file : {file_name} modified time --- {modifed_time}')
            last_modified = modifed_time
            try:
                # send the Metadata
                filemeta = f'{file_name}{separator}{file_path}{separator}{file_size}'
                host_send_sock.send(filemeta.encode())

                # receive ACK from host
                _ = host_send_sock.recv(buffer_size).decode()

                # read the file
                fl = open(file_path_on_local, 'r')
                file_content = fl.read()

                # send the file
                host_send_sock.sendall(file_content.encode())
                # close file
                fl.close()
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


if __name__ == '__main__':

    # host server config
    host_ip = '0.0.0.0'
    host_recv_port = 5001
    host_send_port = 5002
    buffer_size = 1024
    separator = '<SEPARATOR>'
    default_editor = 'code'

    # connect to the host as a client and receive the files
    # save the received files into local_temp dir
    local_temp_dir = '../local_temp'
    # clean the temp before receiving files
    try:
        os.system(f'rm {local_temp_dir}/*')
    except Exception as e:
        print(f'Error in cleaning temp... : {e}')

    # connect to the host to receive file
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host_ip, host_recv_port))

    # Always accept files from host
    try:
        while True:
            sock.send('READY'.encode())

            # receive file's META first
            recv_meta_data = sock.recv(buffer_size).decode()
            # process metadata
            file_name, file_path, file_size = recv_meta_data.split(separator)
            print('metadata revieved from host')

            # Send ACK to host to send file
            sock.send('META_ACK'.encode())

            file_name = file_name.strip()
            file_path = file_path.strip()
            file_size = int(file_size.strip())
            print(f'  [+]Filename : {file_name}')

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

            # open file in default editor
            print(temp_file)
            sp.Popen([default_editor, temp_file])

            # wait for editor to start
            time.sleep(2)

            # start a watcher on the file in a separate thread
            # NOTE: make it as a daemon because when the main process stops, it should also stop all the threads
            x = threading.Thread(target=fileWatcher2, daemon=True,
                                 args=(file_name, file_path, file_size, temp_file))
            x.start()

    except (socket.error, KeyboardInterrupt) as e:
        print(f'[+] Client got some error : {e}\n\tRestart !!!')
        # close socket
        sock.close()
        # exit the client
        sys.exit(0)
