from config_vars import class_vars
from watcher_class import Watcher

def main():
    instance_watcher = Watcher(class_vars)
    instance_watcher.start()

main()