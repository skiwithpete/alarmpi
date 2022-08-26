# Python 3.10 changed how floats are implicitely converted to integers when calling
# the underlying C++ library:

#   It was a change in Python 3.10 to the extension module interface - you can no longer pass a float
#   to an extension function (i.e., a wrapped wxWidgets C++ function) where an int is expected and
#   there would be truncation.
# https://github.com/wxWidgets/Phoenix/issues/2038

# A custom version of WaitingSpinner with explicit float to int conversions
# when needed to prevent "argument 1 has unexpected type 'float'" type errors


from pyqtspinner.spinner import WaitingSpinner


class CustomWaitingSpinner(WaitingSpinner):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def updateTimer(self):
        interval = int(1000 / (self._numberOfLines * self._revolutionsPerSecond))
        self._timer.setInterval(interval)