#!/usr/bin/env python3
"""Natural A folder converter

Converts your music to 432 Hz natural A by slowing it down just a bit.
S.D.G.
"""

# --Modules--
import glob  # File listing
import os
from os import path as op
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import mutagen  # Tag handling
from mutagen import id3
import pydub  # Audio processing


# --Absolute variables--
PITCH_CHANGE = 432 / 440  # Pitch change factor
TUNING_TAG = id3.COMM(encoding=0, text="432 Hz", lang="eng", desc="Tuning")  # The ID3 tag to mark the converted files with
INFOLDER_DEF = os.getcwd()  # Default input folder
OUTFOLDER_DEF = "natural_A_converted"  # Default output folder (subfolder of input folder)
FORMATS = ("wav", "mp3", "m4a", "aac", "ogg", "flac")  # Accepted audio formats
FOLDERPROGRESS_LEN = 100  # Length of folder progress bar


class MainWindow(tk.Tk):
    """Main converter window"""

    def __init__(self):
        """Main converter window"""
        super().__init__()
        self.converter = None
        self.build()
        self.mainloop()

    def build(self):
        """Construct the GUI"""

        self.title("Natural A Music Converter")
        self.lockable_buttons = []  #Buttons to lock out during conversion

        # --Subframe with entry fields for folders, and buttons to browse--
        self.folder_sel_frame = ttk.Frame(self)
        self.folder_sel_frame.grid(row=0, sticky=tk.EW)

        # Infolder selector
        self.infolder = tk.StringVar(self, value=INFOLDER_DEF)  # Variable for input folder path

        ttk.Label(self.folder_sel_frame, text="In folder:").grid(row=0, column=0, sticky=tk.E)

        self.infolder_entry = ttk.Entry(self.folder_sel_frame, textvariable=self.infolder)
        self.infolder_entry.grid(row=0, column=1, sticky=tk.NSEW)

        self.infolder_browse_bttn = ttk.Button(self.folder_sel_frame, text="Browse", command=self.browse_infolder)
        self.infolder_browse_bttn.grid(row=0, column=2, sticky=tk.EW)
        self.lockable_buttons.append(self.infolder_browse_bttn)

        self.recursive = tk.BooleanVar(self)
        self.recursive_checkbttn = ttk.Checkbutton(self.folder_sel_frame, text="Recursive", variable=self.recursive)
        self.recursive_checkbttn.grid(row=0, column=3)
        self.lockable_buttons.append(self.recursive_checkbttn)

        # Outfolder selector
        self.outfolder = tk.StringVar(self)  # Variable for output folder path
        self.outfolder_to_default()

        ttk.Label(self.folder_sel_frame, text="Out folder:").grid(row=1, column = 0, sticky=tk.E)

        self.outfolder_entry = ttk.Entry(self.folder_sel_frame, textvariable=self.outfolder)
        self.outfolder_entry.grid(row=1, column=1, sticky=tk.NSEW)

        self.outfolder_browse_bttn = ttk.Button(self.folder_sel_frame, text="Browse", command=self.browse_outfolder)
        self.outfolder_browse_bttn.grid(row=1, column=2)
        self.lockable_buttons.append(self.outfolder_browse_bttn)

        self.outfolder_default_bttn = ttk.Button(self.folder_sel_frame, text="Default", command=self.outfolder_to_default)
        self.outfolder_default_bttn.grid(row=1, column=3)
        self.lockable_buttons.append(self.outfolder_default_bttn)

        self.folder_sel_frame.columnconfigure(1, weight=1)  # Set center column (the one with the fields) to expand sideways)

        # --Progress bars--
        self.folderprogress = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=FOLDERPROGRESS_LEN, mode="determinate")
        self.folderprogress.grid(row=1, sticky=tk.EW)

        self.fileprogress = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=3, mode="indeterminate")
        self.fileprogress.grid(row=2, sticky=tk.EW)

        # --Status display--
        self.status = tk.StringVar(self, value="Ready.")
        ttk.Label(self, textvariable=self.status).grid(row=3)

        # --Convert button--
        self.convert_bttn = ttk.Button(self)  # , text = "Convert", command = self.start_conversion)
        self.convert_bttn_modeset(True)
        self.convert_bttn.grid(row=4, sticky=tk.NSEW)

        # --Expansion rules--
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

    def convert_bttn_modeset(self, mode: bool):
        """Set what the convert button does

        Args:
            mode (bool): True is Convert, False is Cancel."""

        if mode:
            self.convert_bttn["text"] = "Convert"
            self.convert_bttn["command"] = self.start_conversion
        else:
            self.convert_bttn["text"] = "Cancel"
            self.convert_bttn["command"] = self.cancel_conversion

    def outfolder_to_default(self):
        """Default the output folder to a subdirectory of the input folder"""
        self.outfolder.set(op.join(self.infolder.get(), OUTFOLDER_DEF))

    def browse_infolder(self):
        """Browse for input folder"""
        folder = filedialog.askdirectory(title="Browse for input directory")
        if folder:
            self.infolder.set(op.abspath(folder))

    def browse_outfolder(self):
        """Browse for output folder"""
        folder = filedialog.askdirectory(title="Browse for output directory")
        if folder:
            self.outfolder.set(op.abspath(folder))

    def start_conversion(self):
        """Start the conversion process"""
        # Verify folders
        if not (self.verify_infolder() and self.verify_outfolder()):
            return

        # Start conversion thread
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

    def able_buttons(self, val: bool):
        """Set able of all lockable buttons

        Args:
            val (bool): True is enable, False is disable."""

        val = (tk.DISABLED, tk.NORMAL)[val]
        for button in self.lockable_buttons:
            button["state"] = val

    def verify_infolder(self):
        """Verify the infolder"""
        return op.isdir(self.infolder.get())

    def verify_outfolder(self):
        """Verify the out folder"""

        if not op.isdir(self.outfolder.get()):
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
        else:  # Folder exists
            print("Output folder existed, permissions uncertain.")
            return True


class FileConverter(threading.Thread):
    """Convert a list of files to the outdir, and update the gui"""

    def __init__(self, gui: MainWindow, indir: str, outdir: str):
        """Convert a list of files to the outdir, and update the gui.

        Args:
            gui (MainWindow): The parent GUI.
            indir (str): The input directory.
            outdir (str): The output directory."""

        super().__init__(daemon=True)
        self.gui = gui
        self.indir = indir
        self.outdir = outdir
        self.cancel = False
        self.errors = []
        self.files = []

    def run(self):
        """Thread code"""
        self.intro()

        # Get files
        self.files = []
        if self.gui.recursive.get():
            for fn in glob.glob(op.join(self.indir, "**"), recursive=True):
                for fmt in FORMATS:
                    if fn.endswith("." + fmt):
                        self.files.append(fn)

        else:
            for fmt in FORMATS:
                self.files += glob.glob(op.join(self.indir, "*.") + fmt)

        if not self.files:
            self.errors.append("No acceptable files found or permission denied.")

        # Convert all found files
        for i, inname in enumerate(self.files):
            if self.cancel:
                break
            name = op.basename(inname)
            outname = op.join(self.outdir, name)
            if op.exists(outname):
                print(outname, "exists. Skipping.")
                continue

            # Exact outdir per file to preserve recursive structure
            file_outdir = op.dirname(outname)
            try:
                os.makedirs(file_outdir, exist_ok=True)
                self.convert_file(inname, outname, name)
            except Exception as e:
                self.errors.append(f"When converting `{inname}`, {e}")
                if op.exists(outname):
                    os.remove(outname)
            self.gui.folderprogress["value"] = (i + 1) / len(self.files) * FOLDERPROGRESS_LEN
        self.outro()

    def intro(self):
        """Configure the GUI for the conversion process"""
        self.gui.able_buttons(False)
        self.gui.convert_bttn_modeset(False)
        self.gui.fileprogress.start()
        self.gui.status.set("Searching for files...")

    def outro(self):
        """Configure the GUI for having finished the conversion process"""
        self.gui.fileprogress.stop()
        if self.cancel:
            messagebox.showinfo("Operation cancelled", "You cancelled the operation.")
        elif self.errors:
            messagebox.showerror("Completed with errors", "There were errors when converting one or more files:\n- " + "\n- ".join(self.errors))
        else:
            messagebox.showinfo("Operation completed", "Conversion finished successfully.")
        self.gui.folderprogress["value"] = 0
        self.gui.able_buttons(True)
        self.gui.convert_bttn_modeset(True)
        self.gui.status.set("Ready.")

    def convert_file(self, inname, outname, debugname="file"):
        """Convert one file

        Args:
            inname (str): The full path to the input file.
            outname (str): The full path to the output file.
            debugname (str): What to call the file in the GUI."""

        if self.cancel:
            return
        self.gui.status.set(f"Loading `{debugname}`...")
        music = pydub.AudioSegment.from_file(inname)

        if self.cancel:
            return
        self.gui.status.set(f"Changing speed of `{debugname}`...")
        music.frame_rate *= PITCH_CHANGE

        if self.cancel:
            return
        self.gui.status.set(f"Exporting `{debugname}`...")
        try:
            music.export(outname, format=outname.split(".")[-1])
        except PermissionError:
            messagebox.showerror(
                "Permissions error",
                f"Could not create `{outname}` due to permissions error."
                )
            self.cancel = True
            return

        # Copy and control ID3 tags
        self.gui.status.set(f"Setting ID3 tags of `{debugname}`...")
        oldtags = mutagen.File(inname)
        newtags = mutagen.File(outname)
        newtags.tags = oldtags.tags
        newtags.tags.add(TUNING_TAG)
        newtags.save()


mw = MainWindow()
