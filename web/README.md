Add this section of code to your directory /var/www after you have install Apache.

Here are the instructions to get this up and running on your Raspberry Pi.

sudo apt-get update && sudo apt-get upgrade

sudo apt-get install python-dev python-rpi.gpio apache2 php5 libapache2-mod-php5

sudo service apache2 restart

sudo nano /etc/sudoers
 add to bottom of file:  www-data ALL=(root) NOPASSWD:ALL