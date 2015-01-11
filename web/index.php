<html>
<head>
<meta charset="UTF-8" />
  <link rel="stylesheet" type="text/css" href="css/style.css">
</head>


<?php
if (isset($_POST['LightON']))
{
exec("sudo python /home/pi/lighton_1.py");
}
if (isset($_POST['LightOFF']))
{
exec("sudo python /home/pi/lightoff_1.py");
}
if (isset($_POST['PlaySong']))
{
system("find /media/4tb/music/singles -name '*.mp3' | sort --random-sort| mpg123 -@ - -l 1 -g 60");
}
?>

<form method="post">
<button class="btn" name="LightON">Light ON</button>&nbsp;
<button class="btn" name="LightOFF">Light OFF</button><br><br>
<!-- <button class="btn" name="PlaySong">Play a random track</button><br>
-->
</form> 


</html>
