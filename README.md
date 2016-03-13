Welcome to the Alarm Pi code.

It's "A Simple Spoken Weather And News Clock" for your Raspberry Pi.

Please feel free to take it, and do what you will with it.

This project is the culmination of 3 separate projects:

An overview can be seen here:  https://youtu.be/-Or5jmBqsNE

And see the details of each of the three parts.

1) Alarm clock https://youtu.be/julETnOLkaU 

2) Light https://youtu.be/WpM1aq4B8-A

3) NAS https://youtu.be/T5eKBfstpI0

*required packages:*

`sudo apt-get install python-feedparser python-dnspython mpg123 festival`


*optional packages* (not all commands will work in all environments):

For Ivona support:
`sudo pip install pyvona`


For pico2wave support (this does not work as of 2016/03/13, but may work in the future -- see below for alternate instructions)

`sudo apt-get install libttspico-utils`


**YOU MUST USE RAMFS to avoid wear on your card and to enable Google Voice.**

```shell
sudo mkdir -p /mnt/ram
echo "ramfs       /mnt/ram ramfs   nodev,nosuid,nodiratime,size=64M,mode=1777   0 0" | sudo tee -a /etc/fstab 
sudo mount -a
```

*If you wish to use Ivona voice from Amazon you must get a beta test account at:* 

https://www.ivona.com/us/account/speechcloud/creation/

1. Open an account 
2. Generate credentials
3. Put accesskey and secretkey in config file


*and finally to set your alarm for 733AM Mon-Fri*

`crontab -e 33 7 * * 1-5 /home/pi/alarmpi/sound_the_alarm.py`


*Alternate install for pico2wave:*


If you need to build it yourself don't worry, it's easy. I thieved most of these instructions from [here](http://rpihome.blogspot.com/2015/02/installing-pico-tts.html). But that was written for wheezy and I found that it was a little trickier with jessie. Here we go:

First of all you need to open the file /etc/apt/sources.list and check it contains (the last line should be uncommented) the following lines:

```shell
deb http://mirrordirector.raspbian.org/raspbian/ jessie main contrib non-free rpi
# Uncomment line below then 'apt-get update' to enable 'apt-get source'
deb-src http://archive.raspbian.org/raspbian/ jessie main contrib non-free rpi```

Then as it says in the comment, do:

`sudo apt-get update`

Now, in the alarmpi project we are instructed to make a ramdrive and mount it on /mnt/ram -- I do a lot of my work here because it saves the SD card some wear and tear. This assumes that is already in place -- note that this should be mounted **without** the noexec option. Modify as you wish.

```shell
mkdir -p /mnt/ram/pico_build
cd /mnt/ram/pico_build
apt-get source libttspico-utils
cd svox-1.0+git*
```

In your favorite editer, modify the file debian/control such that it no longer specifies the automake version. That is change the line that looks like this:

`Build-Depends: debhelper (>= 9~), automake1.11, autoconf, libtool, help2man, libpopt-dev, hardening-wrapper`

So that it looks like this:

`Build-Depends: debhelper (>= 9~), automake, autoconf, libtool, help2man, libpopt-dev, hardening-wrapper`

And save it. Then you can do this:

```shell
sudo dpkg-buildpackage -rfakeroot -us -uc
cd ..
sudo dpkg -i libttspico-data_*
sudo dpkg -i libttspico0_*
sudo dpkg -i libttspico-utils_*i
```

That should be it. Note that if you get a permission denied error, your /mnt/ram was mounted with the noexec option set in fstab. Build somewhere else.

You can test your install like this:

```shell
pico2wave -w test.wav "it works! "
aplay test.wav
```

Cheers!
 


- Thanks again to Michael Kidd for adding the config file and giving this project a real structure.  
- Thanks also to Viktor Bjorklund for adding Ivona support.
- Thanks to Craig Pennington for adding pico2wave support and some housekeeping.


