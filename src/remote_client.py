#!/usr/local/bin/python3
""" remote side client process """
import configparser
import os
import platform
import socket
import subprocess as sp
import sys
import threading
import time


def configSetup():
    config = configparser.ConfigParser()
    hostIp = ''
    editor = ''
    # check the file
    if not os.path.exists(r'.host_config.ini'):
        # create the file
        config.add_section('host')
        address = input('Enter the host address :').strip()
        config['host']['address'] = address
        hostIp = address

        config.add_section('editor')
        ed = input('Enter editor\' Executable path : ').strip()
        config['editor'][platform.system()] = ed
        editor = ed

        with open(r'.host_config.ini', 'w') as configfile:
            config.write(configfile)
    else:
        config.read(r'.host_config.ini')

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

        # write all the first inputs into the file
        with open(r'.host_config.ini', 'w') as configfile:
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
                            print(f'[+] File : {file_name} Saved successfully!!')
                        else:
                            print(
                                f'[+] Error while saving the file : {file_ack}\n [+][+] Resolve the issue and save it again to resend')
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


'''
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
'''

if __name__ == '__main__':

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
        print(f'[+] Created temp folder : {local_temp_dir}')
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
        print('[+] connected to host to receive file ')
    except socket.error as e:
        print(f'[!] Error in connecting to host : {e}')
        print('[x] Could not connect to host, BYE !!!')
        time.sleep(3)
        sys.exit(1)

    # Always accept files from host
    while True:
        try:
            sock.send('READY'.encode())

            # receive file's META first
            recv_meta_data = sock.recv(buffer_size).decode()
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

            print(f'  [+] Filename : {file_name}')

            # open file in default editor
            sp.Popen([default_editor, temp_file])

            # wait for editor to start
            time.sleep(2)

            # record the file
            files_rec[file_name] = (file_path, os.path.getmtime(temp_file))

            # x = threading.Thread(target=fileWatcher2, daemon=True,
            #                      args=(host_ip, file_name, file_path, files_rec, temp_file))
            # x.start()

        except (socket.error, KeyboardInterrupt) as e:
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
                        break
                    except socket.error as err:
                        print(f'[!] Client got some error : {err}')
                        continue
                else:
                    continue
            # if comes here then you are connected again continue
            continue
