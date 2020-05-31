#!/usr/local/bin/python3
''' Main Server Process '''


import socket
import threading
import queue


def ListenThread(sock, name, files2sendQ):
    ''' deamon thread '''
    print(f'Listning on {name} connection...')
    threads = []
    
    while True:
        sock.listen(10)
        print(f'Waiting connection on {name}...')
        (client_sock, (ip,port)) = sock.accept()
        print(f'Got connection from {ip}:{port}')

        ''' start a new thread to handle multiple requests '''
        
        threadID = None
        arg = (client_sock, ip, port, files2sendQ)

        if name == 'host2host':
            threadID = host2hostFileRecv
        elif name == 'local2host':
            threadID = local2hostFileRecv
            arg = (client_sock, ip, port)
        elif name == 'host2local':
            threadID = host2localFileSendWorker

           
        x = threading.Thread(target=threadID, args=arg)
        x.start()
        threads.append(x)
    
    for i in threads:
        i.join()
    


def host2hostFileRecv(client_sock, ip, port, files2sendQ):
    ''' host2host file receive thread function '''

    separator = '<SEPARATOR>'
    BUFFER_SIZE = 1024
    
    ''' receive the file_name, file_path and file_size separated by <separator> '''
    rec_data = client_sock.recv(BUFFER_SIZE).decode()
    file_name, file_path, file_size = rec_data.split(separator)
    
    file_name = file_name.strip()
    file_path = file_path.strip()

    # file_size = int(file_size.strip()) 
    # TODO: ValueError: invalid literal for int() with base 10: '72{\n "cells": [],\n "metadata": {},\n "nbformat": 4,\n "nbformat_minor": 4\n}'
    # print(f'\n\n-----file size --{file_size}--\n\n')

    # read the file
    f = open(file_path, 'r')
    file_content = f.read()
   
    # put the file and its meta_data into queue
    files2sendQ.put((rec_data, file_content))

    f.close()

    print('File sent into Queue ... ')
    print(f'Queue size : {files2sendQ.qsize()}')


def local2hostFileRecv(client_sock, ip, port):
    ''' receive file from remote client which has been edited and save
        it to the host's file's actual location 
    '''
    
    separator = '<SEPARATOR>'
    BUFFER_SIZE = 1024

    ''' receive the file_name, file_path and file_size separated by <separator> '''
    rec_data = client_sock.recv(BUFFER_SIZE).decode()
    file_name, file_path, file_size = rec_data.split(separator)
    
    file_name = file_name.strip()
    file_path = file_path.strip()

    # file_size = int(file_size.strip()) 
    # TODO: ValueError: invalid literal for int() with base 10: '72{\n "cells": [],\n "metadata": {},\n "nbformat": 4,\n "nbformat_minor": 4\n}'
    # print(f'\n\n-----file size --{file_size}--\n\n')

    ''' START receiving file from the cleint '''

    # temp file which will be copied to the original locations
    temp_file_path = f'../fromLocal/{file_name}'

    f = open(temp_file_path, 'wb')
    while True:
        bytes_read = client_sock.recv(BUFFER_SIZE)
        if not bytes_read:
            # close the file 
            f.close()
            # file transmission is done 
            break
        # write to the temp file 
        f.write(bytes_read)
    
    # TODO: copy the temp file to the orginal file_path
    # handle the error if the file is not checked out 


def host2localFileSendWorker(client_sock, ip, port, files2sendQ):
    # buffer_size = 1024

    # TODO: add a socket check before reading data from the queue
    while True:
        print('Start sending file ...')
        item = files2sendQ.get()
        file_meta, file_content = item
        
        # send file's meta data
        client_sock.send(bytes(file_meta, 'utf-8'))
        # send the file 
        client_sock.sendall(bytes(file_content, 'utf-8'))

        files2sendQ.task_done()
        print('File sent to remote ...')

    


if __name__ == '__main__':

    ''' ip address of the server process '''
    TCP_IP = '0.0.0.0'
    # TCP_IP = socket.gethostname()

    ''' different ports for different sockets '''
    host2local_port = 5001
    local2host_port = 5002
    host2host_port = 5003
    BUFFER_SIZE = 1024

    ''' setup all the sockets '''

    ''' HOST --> REMOTE '''
    host2local_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    ''' REMOTE --> HOST (multithread) '''
    local2host_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    ''' HOST --> HOST (FOR --> REMOTE)  (MULTITHREAD) '''
    host2host_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    ''' bind all the sockets '''
    host2local_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    local2host_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    host2host_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    host2local_sock.bind((TCP_IP, host2local_port))
    host2host_sock.bind((TCP_IP, host2host_port))
    local2host_sock.bind((TCP_IP, local2host_port))

    print('All the sockets are open and binded ... ')


    # Queue for the files and send it to remote one by one
    files2sendQ = queue.Queue()

    ''' Listening Deamons ''' 
    th1 = threading.Thread(target=ListenThread , args=(host2host_sock, 'host2host', files2sendQ))
    th2 = threading.Thread(target=ListenThread , args=(local2host_sock, 'local2host', files2sendQ))
    th3 = threading.Thread(target=ListenThread , args=(host2local_sock, 'host2local', files2sendQ))
    th1.start()
    th2.start()
    th3.start()

    print('Listening threads started ... ')

    # wait for all the listners
    th1.join()
    th2.join()
    th3.join()
