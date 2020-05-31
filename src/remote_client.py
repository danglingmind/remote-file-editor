#!/usr/local/bin/python3
''' Main Remote client Process '''

import socket
import threading


if __name__ == '__main__':

    ''' host server config '''
    host_ip = '0.0.0.0'
    host_recv_port = 5001
    host_send_port = 5002
    buffer_size = 1024
    separator = '<SEPARATOR>'

    # connect to the host as a client and receive the files
    # save the received files into local_temp dir
    local_temp_dir = '../local_temp'

    # connect to the host
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host_ip, host_recv_port))

    # receive file meta first
    recv_meta_data = sock.recv(buffer_size).decode()
    print(recv_meta_data)

    file_name, file_path, file_size = recv_meta_data.split(separator)

    print(f'File meta received !!!')

    file_name = file_name.strip()
    file_path = file_path.strip()
    file_size = int(file_size.strip())

    print(f'Filename : {file_name}')
    print(f'Filepath : {file_path}')
    print(f'Filesize : {file_size}')

    # save the file into local temp dir
    f = open(f'{local_temp_dir}/{file_name}', 'wb')
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
        
    print(f'File saved into temp dir!!!')
    # TODO: open this file to any editor

   