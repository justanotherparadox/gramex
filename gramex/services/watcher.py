'''
The file watch service uses `watchdoc <https://pythonhosted.org/watchdog/>`_ to
monitor files, and run functions when the file changes.
'''

import logging
from pathlib import Path
from collections import defaultdict
from orderedattrdict import AttrDict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# There's only one observer. Start it at the beginning and schedule stuff later
observer = Observer()
observer.start()

# A mapping of {name: FileEventHandler}
handlers = AttrDict()


class FileEventHandler(FileSystemEventHandler):
    def __init__(self, paths=[], **events):
        super(FileEventHandler, self).__init__()

        self.paths = defaultdict(set)
        self.watches = []

        for path in paths:
            path = Path(path)
            parent = path.parent
            if parent.exists():
                self.paths[parent.resolve()].add(str(path))
            else:
                logging.warn('Parent directory does not exist: %s', path)

        self.__dict__.update(events)
        for directory, path in self.paths.items():
            self.watches.append(observer.schedule(self, str(directory)))

    def dispatch(self, event):
        if any(event.src_path in paths for paths in self.paths.values()):
            super(FileEventHandler, self).dispatch(event)

    def unschedule(self):
        for watch in self.watches:
            observer.unschedule(watch)


def watch(name, paths, **events):
    '''
    Watch one or more paths, and trigger an event function.

    Example::

        watch('test', 'test.txt',
              on_modified: lambda event: logging.info('Modified test.txt'),
              on_created: lambda event: logging.info('Created test.txt'))

    When ``test.txt`` is modified or created, it logs one of the above messages.

    To replace the same handler with another, use the same ``name``::

        watch('test', 'test.txt',
              on_deleted: lambda event: logging.info('Deleted test.txt'))

    Now, when ``test.txt`` is deleted, it logs a message. But when ``test.txt``
    is created or modified, no message is shown, since the old handler has been
    replaced.

    :arg string name: Unique name of the watch.  To replace an existing watch,
        re-use the same name.
    :arg list paths: List of relative or absolute paths to watch.  The paths
        can be strings or ``pathlib.Path`` objects.
    :arg function on_modified(event): Called when any path is modified.
    :arg function on_created(event): Called when any path is created.
    :arg function on_deleted(event): Called when any path is deleted.
    :arg function on_moved(event): Called when any path is moved.
    :arg function on_any_event(event): Called on any of the above events.
    '''
    if name in handlers:
        handlers[name].unschedule()
    handlers[name] = FileEventHandler(paths, **events)