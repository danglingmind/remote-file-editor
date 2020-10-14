#!/usr/local/bin/python3
''' Send the file to host main process which will forward the
    file to remote client '''

import os
import socket
import sys

if __name__ == '__main__':
    ''' ip of the server to which we need to send the file '''
    # check for the file name given as command line args
    if len(sys.argv) < 2:
        print('No file given !!!')
        sys.exit(0)

    # server config
    # server_ip = '0.0.0.0'
    server_ip = socket.gethostname()
    port = 5003
    buffer_size = 1024
    separator = '<SEPARATOR>'

    try:
        # connect to the socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server_ip, port))

        # get the absolute path
        fullpath = os.path.abspath(sys.argv[1].strip())
        print('fullpath : ' + str(fullpath))
        file_path = fullpath
        file_name = file_path.split('/')[-1]
        file_size = os.path.getsize(file_path)
        filemeta = file_name + separator + file_path + separator + str(file_size)
        filemeta = filemeta.strip().encode()
        _ = sock.recv(buffer_size).decode()
        # first send the meta of the file ie. filename, filepath, filesize
        sock.send(filemeta)
        print('File Queued !!!')
        _ = sock.recv(buffer_size).decode()
    except socket.error as e:
        print('[+] Service or Path is not available !!!')
