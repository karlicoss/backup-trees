import logging

import requests


class YandexDisk:
    def __init__(self, token: str):
        self.session = requests.session()
        self.session.headers.update({
            'Authorization': 'OAuth ' + token,
        })
        self.logger = logging.getLogger('YandexDisk')

    def http_get(self, url: str, *args, **kwargs):
        return self.session.get(url, *args, **kwargs)

    def http_put(self, url: str, *args, **kwargs):
        return self.session.put(url, *args, **kwargs)

    def _get_upload_url(self, disk_path: str):
        return self.session.get(
            'https://cloud-api.yandex.net/v1/disk/resources/upload',
            params={
                'path': disk_path,
                'overwrite': True,
            }
        )

    def upload_file(self, data, disk_path: str):
        json = self._get_upload_url(disk_path).json()
        url = json['href']
        self.logger.debug("Uploading to " + url)
        self.http_put(url, data=data)
