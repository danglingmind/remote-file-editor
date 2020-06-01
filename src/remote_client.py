#!/usr/local/bin/python3
''' Main Remote client Process '''

import socket
import threading
import subprocess as sp 
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

def sendFile2Host(src_path):
    print(f'Sending file {src_path}...')

def onModifiedAction(event):
    ''' Send the file back to the host '''
    sendFile2Host(event.src_path)

def fileWatcher(directoryToWatch, filename, filepath):
    ''' Deamon to watch on_modified event for the file that get modified
        on occurance of the event upload the file back
    '''
    patterns = f'*/{filename}'
    ignore_patterns = ""
    ignore_directories = True
    case_sensitive = True
    my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, 
                        ignore_directories, case_sensitive)
                    
    my_event_handler.on_modified = onModifiedAction

    # start watch 
    # observer 
    path = "../local_temp"
    go_recursively = False
    my_observer = Observer()
    my_observer.schedule(my_event_handler, path, recursive=go_recursively)

    my_observer.start()
    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     my_observer.stop()
    #     my_observer.join()

    # stop the observer on file close in editor
    
    my_observer.join()


if __name__ == '__main__':

    ''' host server config '''
    host_ip = '0.0.0.0'
    host_recv_port = 5001
    host_send_port = 5002
    buffer_size = 1024
    separator = '<SEPARATOR>'
    default_editor = 'code'

    # connect to the host as a client and receive the files
    # save the received files into local_temp dir
    local_temp_dir = '../local_temp'

    # connect to the host
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host_ip, host_recv_port))

    # record of watchers
    watchers = []
    # Always accept files from host
    while True:
        # receive file's META first
        recv_meta_data = sock.recv(buffer_size).decode()

        # Send ACK to host to send file 
        sock.send(bytes('META_ACK', 'utf-8'))

        file_name, file_path, file_size = recv_meta_data.split(separator)

        file_name = file_name.strip()
        file_path = file_path.strip()
        file_size = int(file_size.strip())
        print(f'[+]Receiving file...')
        print(f'  [+]Filename : {file_name}')
        print(f'  [+]Filepath : {file_path}')
        print(f'  [+]Filesize : {file_size}')

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
            # TODO: add the check for already existing files and perform 
            # reload or another open option
            f.write(bytes_read)
        f.close()
        print(f'[+]{file_name} saved into {local_temp_dir}!!!')
        # Open this file in default editor
        sp.Popen([default_editor, temp_file])

        # start a watcher for the file which will send file back to host on modification
        watchers.append(threading.Thread(
            target=fileWatcher, 
            args=(local_temp_dir, file_name, file_path)).
            start())
    
    for th in watchers:
        th.join()
   