#!/usr/bin/env python3
"""Natural A folder converter

Converts your music to 432 Hz natural A by slowing it down just a bit.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see <https://www.gnu.org/licenses/>.

S.D.G.
"""

# --Modules--
import os
from os import path as op
from pathlib import Path
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import mutagen  # Tag handling
from mutagen import id3
import pydub  # Audio processing


# --Absolute variables--
PITCH_CHANGE = 432 / 440  # Pitch change factor

# The ID3 tag to mark the converted files with
TUNING_TAG = id3.COMM(encoding=0, text="432 Hz", lang="eng", desc="Tuning")

INFOLDER_DEF = os.getcwd()  # Default input folder

# Default output folder (subfolder of input folder)
OUTFOLDER_DEF = "natural_A_converted"

# Can we handle codecs other than WAV (becomes a str or None)?
CODEC_HANDLER = shutil.which("ffmpeg") or shutil.which("avconv")

# Accepted audio formats
FORMATS = (
    (".wav"),
    (".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac"),
    )[bool(CODEC_HANDLER)]

FOLDERPROGRESS_LEN = 100  # Length of folder progress bar


class MainWindow(tk.Tk):
    """Main converter window"""

    def __init__(self):
        """Main converter window"""
        super().__init__()

        # --Variables that the GUI will use--
        # Variable for input folder path
        self.__indir = tk.StringVar(self, value=INFOLDER_DEF)
        # Variable for output folder path
        self.__outdir = tk.StringVar(self)

        self.converter = None
        self.build()

        # Check if we have FFmpeg
        if not CODEC_HANDLER:
            messagebox.showwarning(
                "FFmpeg not found",
                "The system did not find FFmpeg (or the LibAV equivalent) " +
                "on PATH. Program will only convert WAV files."
                )
        self.mainloop()

    @property
    def indir(self) -> Path:
        """The input directory setting"""
        return Path(op.abspath(self.__indir.get()))

    @indir.setter
    def indir(self, new: str | Path):
        """The input directory setting"""
        self.__indir.set(op.abspath(new))

    @property
    def outdir(self) -> Path:
        """The output directory setting"""
        return Path(op.abspath(self.__outdir.get()))

    @outdir.setter
    def outdir(self, new: str | Path):
        """The output directory setting"""
        self.__outdir.set(op.abspath(new))

    def build(self):
        """Construct the GUI"""

        self.title("Natural A Music Converter")
        self.lockable_buttons = []  # Buttons to lock out during conversion

        # --Subframe with entry fields for folders, and buttons to browse--
        self.folder_sel_frame = ttk.Frame(self)
        self.folder_sel_frame.grid(row=0, sticky=tk.EW)

        # Infolder selector

        ttk.Label(self.folder_sel_frame, text="In folder:").grid(row=0, column=0, sticky=tk.E)

        self.indir_entry = ttk.Entry(self.folder_sel_frame, textvariable=self.__indir)
        self.indir_entry.grid(row=0, column=1, sticky=tk.NSEW)

        self.indir_browse_bttn = ttk.Button(self.folder_sel_frame, text="Browse", command=self.browse_indir)
        self.indir_browse_bttn.grid(row=0, column=2, sticky=tk.EW)
        self.lockable_buttons.append(self.indir_browse_bttn)

        self.recursive = tk.BooleanVar(self)
        self.recursive_checkbttn = ttk.Checkbutton(self.folder_sel_frame, text="Recursive", variable=self.recursive)
        self.recursive_checkbttn.grid(row=0, column=3)
        self.lockable_buttons.append(self.recursive_checkbttn)

        # Outfolder selector
        self.outdir_to_default()

        ttk.Label(self.folder_sel_frame, text="Out folder:").grid(row=1, column=0, sticky=tk.E)

        self.outdir_entry = ttk.Entry(self.folder_sel_frame, textvariable=self.__outdir)
        self.outdir_entry.grid(row=1, column=1, sticky=tk.NSEW)

        self.outdir_browse_bttn = ttk.Button(self.folder_sel_frame, text="Browse", command=self.browse_outdir)
        self.outdir_browse_bttn.grid(row=1, column=2)
        self.lockable_buttons.append(self.outdir_browse_bttn)

        self.outdir_default_bttn = ttk.Button(self.folder_sel_frame, text="Default", command=self.outdir_to_default)
        self.outdir_default_bttn.grid(row=1, column=3)
        self.lockable_buttons.append(self.outdir_default_bttn)

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

    def outdir_to_default(self):
        """Default the output folder to a subdirectory of the input folder"""
        self.outdir = op.join(self.indir, OUTFOLDER_DEF)

    def browse_indir(self):
        """Browse for input folder"""
        folder = filedialog.askdirectory(title="Browse for input directory")
        if folder:
            self.indir = folder

    def browse_outdir(self):
        """Browse for output folder"""
        folder = filedialog.askdirectory(title="Browse for output directory")
        if folder:
            self.outdir = folder

    def start_conversion(self):
        """Start the conversion process"""
        # Verify folders
        if not (self.verify_indir() and self.verify_outdir()):
            return

        # Start conversion thread
        if self.converter:
            self.converter.join()
        self.converter = FileConverter(self, self.indir, self.outdir)
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

    def verify_indir(self):
        """Verify the indir"""
        if self.indir == self.outdir:
            messagebox.showerror("Input directory invalid", "Input and output directories must be different.")
            return False
        if not self.indir.is_dir():
            messagebox.showerror("Input directory invalid", "Input directory does not exist.")
            return False
        if not os.access(self.indir, os.R_OK):
            messagebox.showerror("Permissions error", "Input directory is not readable to this user.")
            return False

        return True

    def verify_outdir(self):
        """Verify the out folder"""

        if self.indir == self.outdir:
            messagebox.showerror("Output directory invalid", "Input and output directories must be different.")
            return False

        # The output folder may not exist
        if not self.outdir.is_dir():
            # If it doesn't, we must create it
            if messagebox.askyesno("Output folder nonexistent", "The selected output folder does not exist. Create?"):
                try:
                    os.makedirs(self.outdir)
                    return True
                except PermissionError:
                    messagebox.showerror("Permissions error", f"Could not create `{self.outdir}` due to permissions error.")
                    self.outdir_to_default()
                    return False

            # If the user refuses to create it, we cannot continue
            else:
                print("Output folder did not exist, auto-creation was declined by user.")
                return False

        # The folder already exists, but we cannot write to it
        if not os.access(self.outdir, os.W_OK):
            messagebox.showerror("Permissions error", "Output directory is not writeable to this user.")
            return False

        return True


class FileConverter(threading.Thread):
    """Convert a list of files to the outdir, and update the gui"""

    def __init__(self, gui: MainWindow, indir: Path, outdir: Path):
        """Convert a list of files to the outdir, and update the gui.

        Args:
            gui (MainWindow): The parent GUI.
            indir (Path): The input directory.
            outdir (Path): The output directory."""

        super().__init__(daemon=True)
        self.gui = gui
        self.indir = indir
        self.outdir = outdir
        self.cancel = False
        self.fails = 0
        self.skips = 0
        self.completions = 0
        self.files = []

    def run(self):
        """Thread code"""
        self.intro()

        # Get files
        self.files = []
        # Scan for all files and folders, optionally digging recursively
        for fp in self.indir.glob("*" + "*" * self.gui.recursive.get(), recurse_symlinks=True):
            # If the scanned item is a file, the suffix is a valid format, and it is not already in the output directory
            if fp.is_file() and fp.suffix.lower() in FORMATS and not fp.is_relative_to(self.outdir):
                self.files.append(fp)

        print(f"Found {len(self.files):,} total files.")

        # Convert all found files
        for i, inname in enumerate(self.files):
            if self.cancel:
                break

            name = op.basename(inname)
            outname = op.join(self.outdir, name)
            if op.exists(outname):
                print(outname, "exists. Skipping.")
                self.skips += 1
                continue

            # Exact outdir per file to preserve recursive structure
            file_outdir = op.dirname(outname)
            try:
                os.makedirs(file_outdir, exist_ok=True)
                self.convert_file(inname, outname, name)
            except Exception as e:
                print(f"Error when converting `{inname}`: {repr(e)}")
                self.fails += 1
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
        elif not self.files:
            messagebox.showerror("No files found", "No supported formats at the input location.")
        elif len(self.files) == self.skips:
            messagebox.showerror("All files already converted", "All found files already existed at the output location or were tagged as converted.")
        elif self.skips:
            messagebox.showwarning("Some files already converted", f"{self.skips:,} found files  already existed at the output location or were tagged as converted.")
        if self.fails:
            messagebox.showerror("Completed with errors", f"{self.fails:,} files failed to convert. See console output for more info.")
        if self.completions:
            messagebox.showinfo("Operation completed", f"Conversion of {self.completions:,} files finished successfully.")
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
        oldtags = mutagen.File(inname)
        if TUNING_TAG in oldtags.values():
            print(f"Tags of `{inname}` say it is already converted.")
            self.skips += 1
            return

        if self.cancel:
            return
        self.gui.status.set(f"Changing speed of `{debugname}`...")
        music.frame_rate *= PITCH_CHANGE

        if self.cancel:
            return
        self.gui.status.set(f"Exporting `{debugname}`...")
        music.export(outname, format=outname.split(".")[-1])

        # Copy and control ID3 tags
        self.gui.status.set(f"Setting ID3 tags of `{debugname}`...")
        newtags = mutagen.File(outname)
        newtags.tags = oldtags.tags
        newtags.tags.add(TUNING_TAG)
        newtags.save()

        # Converting the file is finished
        self.completions += 1


mw = MainWindow()
