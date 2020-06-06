#!/usr/local/bin/python3

import queue
import socket
import threading
import shutil



def host2hostFileRecv(client_sock, files2sendQ):

    separator = '<SEPARATOR>'
    BUFFER_SIZE = 1024


    # receive the file_name, file_path and file_size separated by <separator>
    rec_data = client_sock.recv(BUFFER_SIZE).decode()
    file_name, file_path, file_size = rec_data.split(separator)
    
    file_name = file_name.strip()
    file_path = file_path.strip()

    # read the file
    f = open(file_path, 'r')
    file_content = f.read()
   
    # put the file and its meta_data into queue
    files2sendQ.put((rec_data, file_content))

    f.close()

    # print('File sent into Queue ... ')
    client_sock.close()


def local2hostFileRecv(client_sock):
    separator = '<SEPARATOR>'
    buffer_size = 1024
    print('[+] client to host file receive...')
    # Always receive the file from local
    try:
        while True:
            # receive meta data of the file
            rec_data = client_sock.recv(buffer_size).decode()
            file_name, file_path, file_size = rec_data.split(separator)

            # send ACK for meta data
            client_sock.send('ACK_META'.encode())

            # process meta data
            file_name = file_name.strip()
            file_path = file_path.strip()
            file_size = int(file_size.strip())
            print(f'[+] File name : {file_name}')

            # temp file which will be copied to the original locations
            temp_file_path = f'../fromLocal/{file_name}'

            f = open(temp_file_path, 'wb')
            total_bytes_read = 0
            while total_bytes_read < file_size:
                bytes_read = client_sock.recv(buffer_size)
                total_bytes_read += len(bytes_read)
                if not bytes_read:
                    # close the file
                    f.close()
                    # file transmission is done
                    break
                # write the file
                f.write(bytes_read)
            f.close()
            print(f'[+] {file_name} received from client  ...')

            # copy the temp file to the original file_path
            try:
                shutil.copy(temp_file_path, file_path)
            except Exception as e:
                print(f'Unable to copy {file_name} | Error: {e}')
    except socket.error as e:
        print(f'Error in receiving file from remote: {e}')
        client_sock.close()


def host2localFileSendWorker(client_sock, files2sendQ):
    buffer_size = 1024
    print(f'[+] host to local connected...')
    try:
        while True:
            # receive ready signal
            _ = client_sock.recv(buffer_size).decode()

            # get the item from queue
            item = files2sendQ.get()
            file_meta, file_content = item

            # send file's meta data
            client_sock.send(file_meta.encode())
            # wait for client's ACK for metadata
            _ = client_sock.recv(buffer_size)
            # send the file
            client_sock.sendall(file_content.encode())

            files2sendQ.task_done()

    except socket.error as e:
        print(f'[+] Client error : {e}')
        # push item back to the queue
        files2sendQ.put(item)
        files2sendQ.task_done()
        client_sock.close()
    print('[+] host to local thread closed...')


''' Listeners '''


def host2hostListener(sock, q):
    sock.listen(10)
    while True:
        (cl_sock, (ip, port)) = sock.accept()
        print(f'[+] host to host connected...')
        # start a new thread
        x = threading.Thread(target=host2hostFileRecv, args=(cl_sock, q))
        x.start()


def host2localListener(sock, q):
    sock.listen(10)
    while True:
        (cl_sock, (ip, port)) = sock.accept()
        print(f'[+] host to local connected...')
        # start a new thread
        x = threading.Thread(target=host2localFileSendWorker, args=(cl_sock, q))
        x.start()


def local2hostListener(sock, q):
    sock.listen(10)
    while True:
        (cl_sock, (ip, port)) = sock.accept()
        print(f'[+] local to host connected...')
        # start a new thread
        x = threading.Thread(target=local2hostFileRecv, args=[cl_sock])
        x.start()


if __name__ == '__main__':

    ''' ip address of the server process '''
    # TCP_IP = '0.0.0.0'
    TCP_IP = socket.gethostname()

    # Queue for the files and send it to remote one by one
    files2sendQ = queue.Queue()

    ''' HOST --> HOST '''
    host2host_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host2host_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    host2host_sock.bind((TCP_IP, 5003))
    th1 = threading.Thread(target=host2hostListener, args=(host2host_sock, files2sendQ))
    th1.start()

    ''' HOST --> REMOTE '''
    host2local_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host2local_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    host2local_sock.bind((TCP_IP, 5001))
    th3 = threading.Thread(target=host2localListener, args=(host2local_sock, files2sendQ))
    th3.start()

    ''' REMOTE --> HOST (multithread) '''
    local2host_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local2host_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    local2host_sock.bind((TCP_IP, 5002))
    th2 = threading.Thread(target=local2hostListener, args=(local2host_sock, files2sendQ))
    th2.start()

    # th1.join()
    # th2.join()
    # th3.join()
