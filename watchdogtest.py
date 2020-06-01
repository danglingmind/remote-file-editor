import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import psutil

def on_modified(event):
    print(f'{event.src_path}')

patterns = '*/todo.txt'
ignore_patterns = ""
ignore_directories = True
case_sensitive = True
my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, 
                    ignore_directories, case_sensitive)
                
my_event_handler.on_modified = on_modified

# observer 
path = "."
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

# stop the observer if the file is not open anywhere


my_observer.join()