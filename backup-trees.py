#!/usr/bin/env python3
import logging
from datetime import date

from plumbum import local
from yadisk import YandexDisk


def make_logger():
    logger = logging.getLogger("BackupTrees")
    logger.setLevel(logging.DEBUG)
    return logger

logger = make_logger()

tree = local['tree']


class Backuper:
    _ERROR_OPENING_DIR = '[error opening dir]'  # tree command prints error messages in stdout :(

    def __init__(self, disk, items):
        self.has_error = False

        self.disk = disk
        self.items = items

    def _log_and_notify(self, s: str, level: int=logging.INFO):
        logger.log(level, s)

    def _backup_tree(self, path: str, name: str):
        logger.info("Backing up " + path)
        suffix = str(date.today())
        ret_code, out, err = tree[path].run()
        if ret_code != 0 \
                or err != '' \
                or out.find(Backuper._ERROR_OPENING_DIR, 0, 1000) != -1:  # well, 1000 chars is enough to detect error message

            self.has_error = True
            self._log_and_notify("{}: ERROR\n\treturn code {}\n\terror message {}\n\toutput {}".format(path, ret_code, err, out), level=logging.ERROR)
            return

        data = out
        logger.debug("Dumped the tree...")
        disk_path = 'trees/' + name + "_" + suffix + ".tree.txt"
        logger.debug("Uploading to Disk " + disk_path)
        self.disk.upload_file(data.encode('utf-8'), disk_path)
        self._log_and_notify("{}: SUCCESS".format(path))

    def run(self):
        for path, name in self.items:
            self._backup_tree(path, name)


def main():
    try:
        import coloredlogs
        coloredlogs.install(fmt="%(asctime)s [%(name)s] %(levelname)s %(message)s")
    except ImportError as e:
        if e.name == 'coloredlogs':
            logger.exception(e)
            logger.warning("coloredlogs is not installed. You should try it!")
        else:
            raise e
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    import config
    backuper = Backuper(disk=YandexDisk(config.DISK_ACCESS_TOKEN), items=config.ITEMS)
    backuper.run()

if __name__ == '__main__':
    main()
