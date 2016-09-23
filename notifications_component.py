import notify2


class NotificationsComponent:
    def __init__(self, name: str):
        import os
        os.environ['DISPLAY'] = ':0'  # TODO meh

        # noinspection PyUnresolvedReferences
        from gi.repository import GLib
        self.glib = GLib
        self.main_loop = GLib.MainLoop()
        notify2.init(name, mainloop='glib')

    def start(self):
        # TODO log exceptions?
        self.glib.timeout_add(100, lambda: self.on_start())
        print("STARTING MAIN LOOP")
        self.main_loop.run()

    def finish(self):
        self.on_stop()
        print("FINISHING MAIN LOOP")
        self.main_loop.quit()

    # TODO looks kinda ugly...
    def finish_async(self):
        self.glib.timeout_add(1000, lambda: self.finish())

    def on_start(self):
        raise NotImplementedError

    def on_stop(self):
        raise NotImplementedError

