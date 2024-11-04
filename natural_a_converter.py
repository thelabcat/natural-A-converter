#!/usr/bin/env python3
"""Natural A folder converter

Converts your music to 432 Hz natural A by slowing it down just a bit.
S.D.G.
"""

#--Modules--
import glob #File listing
import os
import threading
from tkinter import *
from tkinter import filedialog, messagebox, ttk
import pydub #Audio processing


#--Absolute variables--
PITCH_CHANGE = 432 / 440 #Pitch change factor
INFOLDER_DEF = os.getcwd() #Default input folder
OUTFOLDER_DEF = "natural_A_converted" #Default output folder (subfolder of input folder)
FORMATS = ("wav", "mp3", "m4a", "aac", "ogg", "flac") #Accepted audio formats
FOLDERPROGRESS_LEN = 100 #Length of folder progress bar

class MainWindow(Tk):
    """Main converter window"""
    def __init__(self):
        """Takes no arguments. Self-mainlooping"""
        super().__init__()
        self.converter = None
        self.build()
        self.mainloop()

    def build(self):
        """Construct the GUI"""

        self.title("Natural A Music Converter")
        self.lockable_buttons = [] #Buttons to lock out during conversion

        #--Subframe with entry fields for folders, and buttons to browse--
        self.folder_sel_frame = Frame(self)
        self.folder_sel_frame.grid(row = 0, sticky = E + W)

        #Infolder selector
        self.infolder = StringVar(self, value = INFOLDER_DEF) #Variable for input folder path

        Label(self.folder_sel_frame, text = "In folder:").grid(row = 0, column = 0, sticky = E)

        self.infolder_entry = Entry(self.folder_sel_frame, textvariable = self.infolder)
        self.infolder_entry.grid(row = 0, column = 1, sticky = N + S + E + W)

        self.infolder_browse_bttn = Button(self.folder_sel_frame, text = "Browse", command = self.browse_infolder)
        self.infolder_browse_bttn.grid(row = 0, column = 2, sticky = E + W)
        self.lockable_buttons.append(self.infolder_browse_bttn)

        self.recursive=BooleanVar(self)
        self.recursive_checkbttn=Checkbutton(self.folder_sel_frame, text = "Recursive", variable = self.recursive)
        self.recursive_checkbttn.grid(row = 0, column = 3)
        self.lockable_buttons.append(self.recursive_checkbttn)

        #Outfolder selector
        self.outfolder = StringVar(self) #Variable for output folder path
        self.outfolder_to_default()

        Label(self.folder_sel_frame, text = "Out folder:").grid(row = 1, column = 0, sticky=E)

        self.outfolder_entry = Entry(self.folder_sel_frame, textvariable = self.outfolder)
        self.outfolder_entry.grid(row = 1, column = 1, sticky = N + S + E + W)

        self.outfolder_browse_bttn=Button(self.folder_sel_frame, text = "Browse", command = self.browse_outfolder)
        self.outfolder_browse_bttn.grid(row = 1, column = 2)
        self.lockable_buttons.append(self.outfolder_browse_bttn)

        self.outfolder_default_bttn = Button(self.folder_sel_frame, text = "Default", command = self.outfolder_to_default)
        self.outfolder_default_bttn.grid(row = 1, column = 3)
        self.lockable_buttons.append(self.outfolder_default_bttn)

        self.folder_sel_frame.columnconfigure(1, weight = 1) #Set center column (the one with the fields) to expand sideways)


        #--Progress bars--
        self.folderprogress=ttk.Progressbar(self, orient=HORIZONTAL, length=FOLDERPROGRESS_LEN, mode = "determinate")
        self.folderprogress.grid(row = 1, sticky = E + W)

        self.fileprogress=ttk.Progressbar(self, orient = HORIZONTAL, length = 3, mode = "indeterminate")
        self.fileprogress.grid(row = 2, sticky = E + W)

        #--Status display--
        self.status=StringVar(self, value = "Ready.")
        Label(self, textvariable = self.status).grid(row = 3)

        #--Convert button--
        self.convert_bttn = Button(self)#, text = "Convert", command = self.start_conversion)
        self.convert_bttn_modeset(True)
        self.convert_bttn.grid(row = 4, sticky = N + S + E + W)

        #--Expansion rules--
        self.columnconfigure(0, weight = 1)
        self.rowconfigure(4, weight = 1)

    def convert_bttn_modeset(self, mode):
        """Set what the convert button does (True is convert, False is cancel)"""
        if mode:
            self.convert_bttn["text"] = "Convert"
            self.convert_bttn["command"] = self.start_conversion
        else:
            self.convert_bttn["text"] = "Cancel"
            self.convert_bttn["command"] = self.cancel_conversion

    def outfolder_to_default(self):
        """Default the output folder to a subdirectory of the input folder"""
        self.outfolder.set(self.infolder.get() + os.sep + OUTFOLDER_DEF)

    def browse_infolder(self):
        """Browse for input folder"""
        folder = filedialog.askdirectory(title = "Browse for input directory")
        if folder:
            self.infolder.set(folder)

    def browse_outfolder(self):
        """Browse for output folder"""
        folder = filedialog.askdirectory(title = "Browse for output directory")
        if folder:
            self.outfolder.set(folder)

    def start_conversion(self):
        """Start the conversion process"""
        #Verify folders
        if not (self.verify_infolder() and self.verify_outfolder()):
            return

        #Start conversion thread
        if self.converter:
            self.converter.join()
        self.converter = FileConverter(self, self.infolder.get(), self.outfolder.get())
        self.converter.start()

    def cancel_conversion(self):
        """Cancel conversion"""
        try:
            self.converter.cancel = True
        except AttributeError:
            print("Converter object does not exist, cannot cancel.")
            return
        self.convert_bttn["text"] = "Cancelling..."

    def able_buttons(self, val):
        """Set able of all lockable buttons"""
        val=(DISABLED, NORMAL)[int(val)]
        for button in self.lockable_buttons:
            button["state"] = val

    def verify_infolder(self):
        """Verify the infolder"""
        return os.path.isdir(self.infolder.get())

    def verify_outfolder(self):
        """Verify the out folder"""
        while self.outfolder.get()[-1] == os.sep:
            self.outfolder.set(self.outfolder.get()[:-1])

        if not os.path.isdir(self.outfolder.get()):
            if messagebox.askyesno("Output folder nonexistent", "The selected output folder does not exist. Create?"):
                try:
                    os.makedirs(self.outfolder.get())
                    return True
                except PermissionError:
                    messagebox.showerror("Permissions error", "Could not create " + self.outfolder.get() + " due to permissions error.")
                    self.outfolder_to_default()
                    return False
            else:
                print("Output folder did not exist, auto-creation was declined by user.")
                return False
        else: #Folder exists
            print("Output folder existed, permissions uncertain.")
            return True


class FileConverter(threading.Thread):
    """Convert a list of files to the outdir, and update the gui"""
    def __init__(self, gui, indir, outdir):
        """Pass the gui, the input directory, and the output directory"""
        super().__init__()
        self.gui = gui
        self.indir = indir
        self.outdir = outdir
        self.cancel = False
        self.errors = []
        self.files = []

    def run(self):
        """Thread code"""
        self.intro()

        #Get files
        self.files = []
        if self.gui.recursive.get():
            for fn in glob.glob(self.indir + os.sep + "**", recursive = True):
                for fmt in FORMATS:
                    if fn.endswith("." + fmt):
                        self.files.append(fn)

        else:
            for fmt in FORMATS:
                self.files += glob.glob(self.indir + os.sep + "*." + fmt)

        if not self.files:
            self.errors.append("No acceptable files found or permission denied.")

        #Convert all found files
        for i, inname in enumerate(self.files):
            if self.cancel:
                break
            name = inname.split(os.sep)[-1]
            outname = inname.replace(self.indir, self.outdir, 1)
            if os.path.exists(outname):
                print(outname, "exists. Skipping.")
                continue
            outdir = outname[: - len(name) - len(os.sep)] #Exact outdir per file to preserve recursive structure
            try:
                os.makedirs(outdir, exist_ok = True)
                self.convert_file(inname, outname, name)
            except Exception as e:
                self.errors.append("When converting " + inname + ", " + str(e))
            self.gui.folderprogress["value"] = int((i + 1) / len(self.files) * FOLDERPROGRESS_LEN)
        self.outro()

    def intro(self):
        """Configure the GUI for the conversion process"""
        self.gui.able_buttons(False)
        self.gui.convert_bttn_modeset(False)
        self.gui.fileprogress.start()
        self.gui.status.set("Searching for files...")

    def outro(self):
        """Configure the GUI for having finished the conversion process"""
        if self.cancel:
            messagebox.showinfo("Operation cancelled", "You cancelled the operation.")
        elif self.errors:
            messagebox.showerror("Completed with errors", "There were errors when converting one or more files:\n- " + "\n- ".join(self.errors))
        else:
            messagebox.showinfo("Operation completed", "Conversion finished successfully.")
        self.gui.folderprogress["value"] = 0
        self.gui.fileprogress.stop()
        self.gui.able_buttons(True)
        self.gui.convert_bttn_modeset(True)
        self.gui.status.set("Ready.")

    def convert_file(self, inname, outname, debugname = "file"):
        """Convert one file"""
        if self.cancel:
            return
        self.gui.status.set("Loading " + debugname + "...")
        music=pydub.AudioSegment.from_file(inname)

        if self.cancel:
            return
        self.gui.status.set("Changing speed of " + debugname + "...")
        music.frame_rate *= PITCH_CHANGE

        if self.cancel:
            return
        self.gui.status.set("Exporting " + debugname + "...")
        try:
            music.export(outname, format = outname.split(".")[-1])
        except PermissionError:
            messagebox.showerror("Permissions error", "Could not create output file " + outname + " due to permissions error.")
            self.cancel = True

mw = MainWindow()
if mw.converter:
    mw.converter.join()
