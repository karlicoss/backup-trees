#!/usr/bin/env python3
import logging
from datetime import date
import sys

from plumbum import local
from yadisk import YandexDisk

from kython import *

tree = local['tree']

class Backuper:
    _ERROR_OPENING_DIR = '[error opening dir]'  # tree command prints error messages in stdout :(

    def __init__(self, disk, items):
        self.has_error = False

        self.disk = disk
        self.items = items

        self.logger = logging.getLogger("BackupTrees")

    def _log_and_notify(self, s: str, level: int=logging.INFO):
        self.logger.log(level, s)

    def _backup_tree(self, path: str, name: str):
        self.logger.info("Backing up " + path)
        suffix = str(date.today())
        ret_code, out, err = tree[path].run()
        if ret_code != 0 \
                or err != '' \
                or out.find(Backuper._ERROR_OPENING_DIR, 0, 1000) != -1:  # well, 1000 chars is enough to detect error message

            self.has_error = True
            self._log_and_notify("{}: ERROR\n\treturn code {}\n\terror message {}\n\toutput {}".format(path, ret_code, err, out), level=logging.ERROR)
            return

        data = out
        self.logger.debug("Dumped the tree...")
        disk_path = 'trees/' + name + "_" + suffix + ".tree.txt"
        self.logger.debug("Uploading to Disk " + disk_path)
        self.disk.upload_file(data.encode('utf-8'), disk_path)
        self._log_and_notify("{}: SUCCESS".format(path))

    def run(self):
        self.logger.info("Using items " + str(self.items))
        for path, name in self.items:
            self._backup_tree(path, name)


def main():
    setup_logging()

    import config
    items = []
    eargs = sys.argv[1:]
    extras = len(eargs)
    if extras > 0:
        for i in range(0, extras, 2):
            items.append((eargs[i], eargs[i + 1]))
    else:
        items = config.ITEMS

    backuper = Backuper(disk=YandexDisk(config.DISK_ACCESS_TOKEN), items=items)
    backuper.run()

if __name__ == '__main__':
    main()
