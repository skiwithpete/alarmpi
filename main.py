#!/usr/bin/env python
# -*- coding: utf-8 -*-


import clock


# Entrypoint for the project, runs the clock GUI. The rest of the components
# (greeting, news and weather, radio) are processed in sound_the_alarm.py. The clock
# can be used to set a cron entry for this. Alternatively, sound_the_alarm.py
# can be run directly.


if __name__ == "__main__":
    app = clock.Clock()
    app.create_main_window()
    app.root.mainloop()
