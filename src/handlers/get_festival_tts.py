import subprocess

from src import aptts

# The Festival TTS client is different from others in that it does not make API calls
# or involve a setup process where the textual content is processed to a playable audio.
# Instead the play method directly plays the alarm.


class FestivalTTSManager(aptts.AlarmpiTTS):

    def setup(self, text):
        """Dummy setup function needed for the aptts model."""
        return text

    def play(self, text):
        cmd = ["echo"] + text.split()
        p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["/usr/bin/festival", "--tts"],
                              stdin=p1.stdout, stdout=subprocess.PIPE)
        p2.wait()
        p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
