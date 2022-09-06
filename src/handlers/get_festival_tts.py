import subprocess
import tempfile

import pydub
import pydub.playback

from src import aptts


class FestivalTTSManager(aptts.AlarmpiTTS):

    def setup(self, text):
        """Convert text to audio using text2wave (part of festival package)."""

        # text2wave output seems to be slightly different when returned as stdout.
        # Use temporary file instead.
        # Maybe a difference in headers/metadata etc?
        with tempfile.NamedTemporaryFile() as f:
            subprocess.run(["/usr/bin/text2wave", "-o", f.name], input=text.encode())
            audio = pydub.AudioSegment.from_wav(f.name)

        return audio
