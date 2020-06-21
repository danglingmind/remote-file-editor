#!/usr/local/bin/python3

import os
import socket
import sys

if __name__ == '__main__':

    if len(sys.argv) < 2:
        print('No file given !!!')
        sys.exit(0)

    server_ip = socket.gethostname()
    port = 5003
    buffer_size = 1024
    separator = '<SEPARATOR>'
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server_ip, port))

        full_path = os.path.abspath(sys.argv[1].strip())
        print(f'[+] File : {full_path}')
        file_path = full_path
        file_name = file_path.split('/')[-1]
        file_size = os.path.getsize(file_path)
        sock.send(f'{file_name}{separator}{file_path}{separator}{file_size}'.encode())
        print('[+] Opening !!!')
    except socket.error as e:
        print(f'[+] Service is not running !!!')
