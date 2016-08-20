#!/usr/bin/env python3
import logging
from datetime import date

import notify2
import requests
from notify2 import Notification
from plumbum import local


# TODO just make builder?
def get_notification(message: str, icon: str, expires: int) -> Notification:
    n = notify2.Notification(
        summary="Trees dumper",
        message=message,
        icon=icon,
    )
    n.set_timeout(expires)
    return n


def get_error_notification(message: str) -> Notification:
    return get_notification(message=message, icon='dialog-error', expires=-1)


def get_info_notification(message: str) -> Notification:
    return get_notification(message=message, icon='dialog-information', expires=10 * 1000)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

tree = local['tree']

ITEMS = [
    ('/L/Dropbox/'              , 'dropbox'),
    ('/L/yandex-disk/'          , 'yandex-disk'),
    ('/L/repos/'                , 'repos'), # todo sanitize output? exclude files at least?
    ('/media/karlicos/Elements/', 'hdd-2tb'),
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
                'path': disk_path,
                'overwrite': True,
            }
        )

    def upload_file(self, data, disk_path: str):
        json = self._get_upload_url(disk_path).json()
        url = json['href']
        logging.debug("Uploading to " + url)
        self.http_put(url, data=data)


class Backuper:
    _ERROR_OPENING_DIR = '[error opening dir]'  # tree command prints error messages in stdout :(

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
        for path, name in ITEMS:
            self._backup_tree(path, name)
        self._get_notification().show()


class NotificationsComponent:
    def __init__(self, name: str):
        import os
        os.environ['DISPLAY'] = ':0'  # TODO meh

        # noinspection PyUnresolvedReferences
        from gi.repository import GLib
        self.main_loop = GLib.MainLoop()
        notify2.init(name, mainloop='glib')

    def start(self):
        # TODO log exceptions?
        # TODO I don't like the order of commands...
        self.onStart()
        self.main_loop.run()

    def finish(self):
        self.onStop()
        logger.info("Finishing GTK loop")
        self.main_loop.quit()

    def onStart(self):
        raise NotImplementedError

    def onStop(self):
        raise NotImplementedError


class BackupTreesComponent(NotificationsComponent):
    def __init__(self):
        super().__init__('trees-dumper')

    def _run_backups(self):
        try:
            Backuper().run()
        except Exception as e:
            logger.exception(e)
            get_error_notification('Exception while running the tool: ' + str(e)).show()

    # TODO read https://developer.gnome.org/notification-spec/
    def onStart(self):
        n = get_notification(message="Run now?", icon='dialog-question', expires=-1)
        n.add_action("error", "<b>Run</b>", lambda n, action: self._run_backups())
        n.add_action("later", "Later", lambda n, action: self.finish())
        n.connect('closed', lambda n: self.finish())
        n.show()

    def onStop(self):
        pass


def main():
    component = BackupTreesComponent()
    component.start()

if __name__ == '__main__':
    main()
