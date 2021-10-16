# Send a debug signal to the main script
kill -s USR1 $(pgrep -f "python .*(alarmpi/)?main.py")
