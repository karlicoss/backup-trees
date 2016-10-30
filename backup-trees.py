#!/usr/bin/env python3
import logging
from datetime import date

from notify2 import Notification, EXPIRES_NEVER
from plumbum import local

from notify2_component import Notify2Component
from yadisk import YandexDisk


def get_notification(message: str, icon: str, expires: int) -> Notification:
    n = Notification(
        summary="Trees dumper",
        message=message,
        icon=icon,
    )
    n.set_timeout(expires)
    return n


def get_error_notification(message: str) -> Notification:
    return get_notification(message=message, icon='dialog-error', expires=EXPIRES_NEVER)


def get_info_notification(message: str) -> Notification:
    return get_notification(message=message, icon='dialog-information', expires=10 * 1000)


def make_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    return logger


logger = make_logger()

tree = local['tree']


class Backuper:
    _ERROR_OPENING_DIR = '[error opening dir]'  # tree command prints error messages in stdout :(

    def __init__(self, disk, items):
        self.notification = []
        self.has_error = False

        self.disk = disk
        self.items = items

    def _log_and_notify(self, s: str):
        self.notification.append(s)
        logger.info(s)

    def _backup_tree(self, path: str, name: str):
        logger.info("Backing up " + path)
        suffix = str(date.today())
        ret_code, out, err = tree[path].run()
        if ret_code != 0 \
                or err != '' \
                or out.find(Backuper._ERROR_OPENING_DIR, 0, 1000) != -1:  # well, 1000 chars is enough to detect error message

            self.has_error = True
            self._log_and_notify("{}: ERROR\n\treturn code {}\n\terror message {}\n\toutput {}".format(path, ret_code, err, out))
            return

        data = out
        logger.info("Dumped the tree...")
        disk_path = 'trees/' + name + "_" + suffix + ".tree.txt"
        logger.info("Uploading to Disk " + disk_path)
        self.disk.upload_file(data.encode('utf-8'), disk_path)
        self._log_and_notify("{}: SUCCESS".format(path))

    def _get_notification(self) -> Notification:
        if self.has_error:
            return get_error_notification('\n'.join(self.notification))
        else:
            return get_info_notification('\n'.join(self.notification))

    def run(self):
        for path, name in self.items:
            self._backup_tree(path, name)
        self._get_notification().show()


class BackupTreesComponent(Notify2Component):
    def __init__(self):
        super().__init__('trees-dumper')
        try:
            from config import DISK_ACCESS_TOKEN, ITEMS
        except ImportError as e:
            raise RuntimeError("Please set up config.py!", e)

        self.backuper = Backuper(disk=YandexDisk(DISK_ACCESS_TOKEN), items=ITEMS)

    def _run_backups(self):
        try:
            self.backuper.run()
        except Exception as e:
            logger.exception(e)
            get_error_notification("Exception while running the tool: " + str(e)).show()

    # TODO read https://developer.gnome.org/notification-spec/
    def on_start(self):
        self._run_backups()
        self.finish_async()

    def on_stop(self):
        pass


def main():
    logger.info("Starting component...")
    BackupTreesComponent().start()

if __name__ == '__main__':
    main()
