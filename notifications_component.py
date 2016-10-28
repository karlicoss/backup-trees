import logging

import notify2


class NotificationsComponent:
    def __init__(self, name: str):
        import os
        os.environ['DISPLAY'] = ':0.0'  # TODO meh

        import gi
        gi.require_version('Gtk', '3.0')
        # noinspection PyUnresolvedReferences
        from gi.repository import GLib
        self.glib = GLib
        self.main_loop = GLib.MainLoop()
        notify2.init(name, mainloop='glib')

    def start(self):
        # TODO log exceptions?
        self.on_start_async()
        logging.info("STARTING MAIN LOOP")
        self.main_loop.run()

    def finish(self):
        self.on_stop()
        logging.info("FINISHING MAIN LOOP")
        self.main_loop.quit()

    def on_start_async(self):
        self.glib.timeout_add_seconds(1, lambda: self.on_start())

    # TODO looks kinda ugly...
    def finish_async(self):
        self.glib.timeout_add_seconds(1, lambda: self.finish())

    def on_start(self):
        raise NotImplementedError

    def on_stop(self):
        raise NotImplementedError

