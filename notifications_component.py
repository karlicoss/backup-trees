import notify2


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
        self.on_start()
        self.main_loop.run()

    def finish(self):
        self.on_stop()
        self.main_loop.quit()

    def on_start(self):
        raise NotImplementedError

    def on_stop(self):
        raise NotImplementedError

