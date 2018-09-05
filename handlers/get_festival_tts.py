#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess


class FestivalTTSManager:
    """Use Festival command line program in tts mode to generate speech."""

    def play(self, text):
        cmd = ["echo"] + text.split()  # split the text to a list and prepend the echo command
        p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        subprocess.Popen(["/usr/bin/festival", "--tts"], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
