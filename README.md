# Remote-file-editor
A simple utility which allows you to open a file into your machine instead of terminal just by a simple command.


It is just like replacing your VIM with your choice of editor.

Just setup the server on remote machine and client on your machine, and you are good to go.

Start the service on remote machine.

To open a file type " $ redit file.txt 

File will open on your machine with your preferred editor, whenever you modify and save the file it will reflected on your 
remote as well.


For Server and client setup follow the instructions inside respective directories.

# Key Features
1. Don't need to browse to the file from client (which I think is most irritating), most of the existing tools like win-scp you can open any file but you need to browse to the file location and then open it, if you have a slow connection then it is horrible.

2. Don't need to explicitly save or upload the file back to the remote server. Our client handles that for you.

3. You can choose your editor.

4. Don't need to interact with client application, you just need to start and then it works seemlessly.

5. If you lost your connection for whatever reason , no need to worry , just go to the temp directory your changed file is there until you close your client.
