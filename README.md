# natural-A-converter
Natural A music converter v1.1

Converts an entire folder of music from 440Hz A to 432Hz A by slowing it down just a bit.

Depends on modules:
pydub (Pip package)
os (native)
glob (native)
tkinter (semi-native)
threading (native)

A simple mass speed changer to convert your music from current industry standart 440Hz A to natural 432Hz A.

Currently supported formats:
- WAV
- MP3
- M4A
- AAC
- OGG
- FLAC

How to use:

0) Ensure Python 3 and all dependencies are installed. You will probably have to run 'pip install pydub' but everything else will probably be installed by default.
1) Download the program, and run it with Python 3.
2) Enter or browse for an input folder of music.
3) Check "Recursive" if you want the program to search and convert subfolders. The hiearchy of music-containing subfolders will be recreated in the output folder.
4) Enter, browse, or click the "Default" button for an output folder. Clicking "Default" will set the output folder to <input folder>/natural_A_converted.
5) Click "Convert."

If you encounter any difficulty that seems like it's not supposed to happen, please let me know by filing an issue. You can also get some debug by running the program from the command line.

Hope this is helpful. Enjoy!

S.D.G.
