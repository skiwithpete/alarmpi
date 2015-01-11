Welcome to the Alarm Pi code.

It's "A Simple Spoken Weather And News Clock" for your Raspberry Pi.

Please feel free to take it, and do what you will with it.

Watch the video here:  http://youtu.be/julETnOLkaU

*required packages:

  sudo apt-get install python-feedparser mpg123 festival

** YOU MUST USE RAMFS to avoid wear on your card and to enable Google Voice.

  sudo mkdir -p /mnt/ram

  echo "ramfs       /mnt/ram ramfs   nodev,nosuid,noexec,nodiratime,size=64M   0 0" | sudo tee -a /etc/fstab 

*** and finally to set your alarm for 733AM Mon-Fri

  crontab -e 33 7 * * 1-5 sudo python /home/pi/sound_the_alarm.pi

Thanks again to Michael Kidd for adding the config file and giving this project a real structure.  
