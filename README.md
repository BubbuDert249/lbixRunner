# lbixRunner
Runs .lbix images <br>
.lbix is a ZIP-based image format, which contains .lbscript (optional) and .lbimg (image) <br>
The lbscript is limited and mostly for images and UI <br>
lbscript commands: <br>
showmsgbox "Window Title", "Message content" --shows a message box <br>
showtxtbox "Window Title", "Message content" --same as showmsgbox but with a text box <br>
txtboxinput --stored input from showtxtbox <br>
setwintitle "Title" --sets the window title <br>
transparency 10 --sets the window transparency (kind of like modern Aero) <br>
wait 2 --waits seconds before running the next command <br>
