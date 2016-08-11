#!/usr/bin/env python3
from datetime import date
import notify2
from pathlib import Path
import logging
import requests
import sys

from plumbum import local


def show_notification(message: str, icon: str, expires: int):
    import os
    os.environ['DISPLAY'] = ':0' # TODO meh

    notify2.init("trees-dumper")
    n = notify2.Notification(
        summary="Trees dumper", 
        message=message,
        icon=icon,
    )
    n.set_timeout(expires)
    n.show()


def show_error_notification(message: str):
    show_notification(message=message, icon='dialog-error', expires=notify2.EXPIRES_NEVER)

def show_info_notification(message: str):
    show_notification(message=message, icon='dialog-information', expires=10000)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

tree = local['tree']

OUTPUT_DIR = Path('/L/backups/trees')

ITEMS = [
    ('/L/Dropbox/'               , 'dropbox'),
    ('/L/yandex-disk/'           , 'yandex-disk'),
    ('/L/repos/'                 , 'repos'), # todo sanitize output? exclude files at least?
    ('/media/karlicos/Elements/' , 'hdd-2tb'), 
]


class YandexDisk:

    def __init__(self, token: str):
        self.session = requests.session()
        self.session.headers.update({
            'Authorization': 'OAuth ' + token,
        })

    def http_get(self, url: str, *args, **kwargs):
        return self.session.get(url, *args, **kwargs)

    def http_put(self, url: str, *args, **kwargs):
        return self.session.put(url, *args, **kwargs)

    def _get_upload_url(self, disk_path: str):
        return self.session.get(
            'https://cloud-api.yandex.net/v1/disk/resources/upload',
            params={
                'path'      : disk_path,
                'overwrite' : True,
            }
        )

    def upload_file(self, data, disk_path: str):
        json = self._get_upload_url(disk_path).json()
        url = json['href']
        logging.debug("Uploading to " + url)
        self.http_put(url, data=data)

class Backuper:

    _ERROR_OPENING_DIR = '[error opening dir]' # tree command prints erro messages in stdout :(

    def __init__(self):
        self.notification = []
        self.has_error = False

        try:
            from config import DISK_ACCESS_TOKEN
        except ImportError as e:
            raise RuntimeError("Please set up config.py!", e)

        self.disk = YandexDisk(DISK_ACCESS_TOKEN)

    def _log_and_notify(self, s: str):
        self.notification.append(s)
        logger.info(s)

    def _backup_tree(self, path: str, name: str):
        logging.info("Backing up " + path)
        suffix = str(date.today())
        ret_code, out, err = tree[path].run()
        if ret_code != 0 \
                or err != '' \
                or out.find(Backuper._ERROR_OPENING_DIR, 0, 1000) != -1: # well, 1000 chars is enough to detect error message

            self.has_error = True
            self._log_and_notify("{}: ERROR\n\treturn code {}\n\terror message {}\n\toutput {}".format(path, ret_code, err, out))
            return

        data = out
        logging.info("Dumped the tree...")
        disk_path = 'trees/' + name + "_" + suffix + ".tree.txt"
        logging.info("Uploading to Disk " + disk_path)
        self.disk.upload_file(data.encode('utf-8'), disk_path)
        self._log_and_notify("{}: SUCCESS".format(path))

    def _show_notification(self):
        if self.has_error:
            show_error_notification('\n'.join(self.notification))
        else:
            show_info_notification('\n'.join(self.notification))

    def run(self):
        for path, name in ITEMS:
            self._backup_tree(path, name)
        self._show_notification()

if __name__ == '__main__':
    try:        
        Backuper().run()
    except Exception as e:
        logger.exception(e)
        show_error_notification('Exception while running the tool: ' + str(e))
