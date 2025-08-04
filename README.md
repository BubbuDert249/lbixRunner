# lbixRunner
Runs .lbix images <br>
.lbix is a ZIP-based image format, which contains .lbscript (optional), .lbimg (image) and .lbicon (icon, if used seticon in .lbscript) <br>
The lbscript is limited and mostly for images and UI <br>
lbscript scripting: <br>
showmsgbox "Window Title", "Message content" --shows a message box <br>
showtxtbox "Window Title", "Message content" --same as showmsgbox but with a text box <br>
txtboxinput --stored input from showtxtbox <br>
setwintitle "Title" --sets the window title <br>
transparency 10 --sets the window transparency (kind of like modern Aero) <br>
wait 2 --waits seconds before running the next command <br>
lbixname --the .lbix name <br>
math 2+2 --a mini calculator <br>
seticon --sets the window icon (.lbicon format, in the .lbix) <br>
# How to build from source: <br>
1. Download at least lbixrunner.py and lbixrunner.spec <br>
2. Install PyInstaller if not installed: <br>
   ```pip install pyinstaller``` <br>
3. Run: <br>
  ```pyinstaller lbixrunner.spec``` <br>
