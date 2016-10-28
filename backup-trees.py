#!/usr/bin/env python3
import logging
from datetime import date

import notify2
from notify2 import Notification, EXPIRES_NEVER
from plumbum import local

from notifications_component import NotificationsComponent
from yadisk import YandexDisk

def get_wifi_name():
    return local['iwgetid']('-r').strip()


def get_notification(message: str, icon: str, expires: int) -> Notification:
    n = notify2.Notification(
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
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)    
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
        logging.info("Backing up " + path)
        suffix = str(date.today())
        ret_code, out, err = tree[path].run()
        if ret_code != 0 \
                or err != '' \
                or out.find(Backuper._ERROR_OPENING_DIR, 0, 1000) != -1:  # well, 1000 chars is enough to detect error message

            self.has_error = True
            self._log_and_notify("{}: ERROR\n\treturn code {}\n\terror message {}\n\toutput {}".format(path, ret_code, err, out))
            return

        data = out
        logging.info("Dumped the tree...")
        disk_path = 'trees/' + name + "_" + suffix + ".tree.txt"
        logging.info("Uploading to Disk " + disk_path)
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


class BackupTreesComponent(NotificationsComponent):
    def __init__(self):
        super().__init__('trees-dumper')
        try:
            from config import DISK_ACCESS_TOKEN, ITEMS, ALLOWED_NETWORKS
        except ImportError as e:
            raise RuntimeError("Please set up config.py!", e)

        self.backuper = Backuper(disk=YandexDisk(DISK_ACCESS_TOKEN), items=ITEMS)
        self.allowed_networks = ALLOWED_NETWORKS

    def _run_backups(self):
        try:
            self.backuper.run()
        except Exception as e:
            logger.exception(e)
            get_error_notification("Exception while running the tool: " + str(e)).show()

    # TODO read https://developer.gnome.org/notification-spec/
    def on_start(self):
        wifi = get_wifi_name()
        if wifi in self.allowed_networks:
            logger.info("Network %s whitelisted, no need for confirmation", wifi)
            # no need to ask
            self._run_backups()
            self.finish_async()
        else:
            logger.info("Network %s is not whitelisted, asking for confirmation", wifi)
            n = get_notification(message="Run now?", icon='dialog-question', expires=EXPIRES_NEVER)
            n.add_action("error", "<b>Run</b>", lambda n, action: self._run_backups())
            n.add_action("later", "Later", lambda n, action: None) # fake button, same as 'closed'
            n.connect('closed', lambda n: self.finish_async())
            n.show()

    def on_stop(self):
        pass


def main():
    logger.info("Starting component...")
    component = BackupTreesComponent()
    component.start()

if __name__ == '__main__':
    main()
