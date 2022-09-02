# Python 3.10 changed how floats are implicitely converted to integers when calling
# the underlying C++ library:

#   It was a change in Python 3.10 to the extension module interface - you can no longer pass a float
#   to an extension function (i.e., a wrapped wxWidgets C++ function) where an int is expected and
#   there would be truncation.
# https://github.com/wxWidgets/Phoenix/issues/2038

# A custom version of WaitingSpinner with explicit float to int conversions
# when needed to prevent "argument 1 has unexpected type 'float'" type errors

# See https://github.com/fbjorn/QtWaitingSpinner/tree/4e344514f69f627e0bcea19191fffb44efbba352
# for original source


from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


from pyqtspinner.spinner import WaitingSpinner


class CustomWaitingSpinner(WaitingSpinner):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def updateTimer(self):
        interval = int(1000 / (self._numberOfLines * self._revolutionsPerSecond))
        self._timer.setInterval(interval)

    def updatePosition(self):
        if self.parentWidget() and self._centerOnParent:
            self.move(
                int(self.parentWidget().width() / 2 - self.width() / 2),
                int(self.parentWidget().height() / 2 - self.height() / 2)
            )

    def paintEvent(self, QPaintEvent):
        self.updatePosition()
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if self._currentCounter >= self._numberOfLines:
            self._currentCounter = 0

        painter.setPen(Qt.NoPen)
        for i in range(self._numberOfLines):
            painter.save()
            painter.translate(self._innerRadius + self._lineLength, self._innerRadius + self._lineLength)
            rotateAngle = float(360 * i) / float(self._numberOfLines)
            painter.rotate(rotateAngle)
            painter.translate(self._innerRadius, 0)
            distance = self.lineCountDistanceFromPrimary(i, self._currentCounter, self._numberOfLines)
            color = self.currentLineColor(
                distance,
                self._numberOfLines,
                self._trailFadePercentage,
                self._minimumTrailOpacity,
                self._color
            )
            painter.setBrush(color)
            painter.drawRoundedRect(
                QRect(0, int(-self._lineWidth / 2), self._lineLength, self._lineWidth),
                self._roundness,
                self._roundness,
                Qt.RelativeSize
            )
            painter.restore()