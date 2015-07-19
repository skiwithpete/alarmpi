Welcome to the Alarm Pi code.

It's "A Simple Spoken Weather And News Clock" for your Raspberry Pi.

Please feel free to take it, and do what you will with it.

This project is the culmination of 3 separate projects:

An overview can be seen here:  https://youtu.be/-Or5jmBqsNE

And see the details of each of the three parts.

1) Alarm clock https://youtu.be/julETnOLkaU 

2) Light https://youtu.be/WpM1aq4B8-A

3) NAS https://youtu.be/T5eKBfstpI0

*required packages:

  sudo apt-get install python-feedparser mpg123 festival

** YOU MUST USE RAMFS to avoid wear on your card and to enable Google Voice.

  sudo mkdir -p /mnt/ram

  echo "ramfs       /mnt/ram ramfs   nodev,nosuid,noexec,nodiratime,size=64M   0 0" | sudo tee -a /etc/fstab 

*** and finally to set your alarm for 733AM Mon-Fri

  crontab -e 33 7 * * 1-5 sudo python /home/pi/sound_the_alarm.pi

Thanks again to Michael Kidd for adding the config file and giving this project a real structure.  
