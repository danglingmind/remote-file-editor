#!/usr/local/bin/python3
''' Send the file to host main process which will forward the 
    file to remote client '''

import socket
import threading
import sys
import os


if __name__ == '__main__':
    ''' ip of the server to which we need to send the file '''
    # check for the file name given as command line args
    if len(sys.argv) < 2 :
        print('No file given !!!')
        sys.exit(0)

    # server config
    server_ip = '0.0.0.0'
    port = 5003
    buffer_size = 1024
    separator = '<SEPARATOR>'

    # connect to the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, port))


    file_path = sys.argv[1].strip()
    file_name = file_path.split('/')[-1]
    file_size = os.path.getsize(file_path)


    # first send the meta of the file ie. filename, filepath, filesize
    sock.send(f'{file_name}{separator}{file_path}{separator}{file_size}'.encode())

    print('File sent !!!')



