#!/usr/bin/env python3
from datetime import date
from pathlib import Path
import requests
import sys

from plumbum import local

tree = local['tree']

OUTPUT_DIR = Path('/L/backups/trees')

ITEMS = [
    ('/L/Dropbox/'     , 'dropbox'),
    ('/L/yandex-disk/' , 'yandex-disk'),
    ('/L/repos/'       , 'repos'), # todo sanitize output? exclude files at least?
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
        print("Uploading to " + url)
        self.http_put(url, data=data)


try:
    from config import DISK_ACCESS_TOKEN
except ImportError:
    print("Please set up config.py!")
    sys.exit(1)

disk = YandexDisk(DISK_ACCESS_TOKEN)

def backup_tree(path: str, name: str):
    print("Backing up " + path)
    suffix = str(date.today())
    disk_path = 'trees/' + name + "_" + suffix + ".tree.txt"
    data = tree(path)
    disk.upload_file(data.encode('utf-8'), disk_path)
    print("Success!")


for path, name in ITEMS:
    backup_tree(path, name)
