import subprocess

from src import aptts


class FestivalTTSManager(aptts.AlarmpiTTS):
    """Use Festival command line program in tts mode to generate speech."""

    def play(self, text):
        cmd = ["echo"] + text.split()  # split the text to a list and prepend the echo command
        p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["/usr/bin/festival", "--tts"],
                              stdin=p1.stdout, stdout=subprocess.PIPE)
        p2.wait()
        p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
