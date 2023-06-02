import os
import platform
import sys
import threading
import tkinter
import tkinter.filedialog
import tkinter.messagebox

import psutil
import validators

from scripts.image import download_images
from scripts.video import download_videos


def resource_path(relative_path):
	""" Get absolute path to resource, works for dev and for PyInstaller """
	try:
		# PyInstaller creates a temp folder and stores path in _MEIPASS
		base_path = sys._MEIPASS
	except AttributeError:
		base_path = os.path.abspath(".")
	return os.path.join(base_path, relative_path)

class App:
	def __init__(self):

		self.width = 700
		self.height = 300

		self.root = tkinter.Tk()
		self.root.title("Media Scraper")
		self.root.geometry(f"{self.width}x{self.height}+{(self.root.winfo_screenwidth() - self.width) // 2}+{(self.root.winfo_screenheight() - self.height) // 2}")
		self.root.resizable(False, False)
		self.root.iconbitmap(resource_path("data/download_icon.ico") if platform.system() != "Darwin" else resource_path("data/download_icon_mac.icns"))
		self.root.config(bg="#ffc028")

		self.title = tkinter.Label(self.root, text="Media Scraper", font=("Gabriola", 50, "bold"), bg="#ffc028", fg="#ffffff")
		self.title.place(x=0, y=5, width=self.width, height=100)

		self.link_title = tkinter.Label(self.root, text="Link:", font=("Helvetica", 17, "bold"), bg="#ffc028", fg="#ffffff")
		self.link_title.place(x=37, y=83, width=60, height=100)
		self.link_scrollbar = tkinter.Scrollbar(self.root, orient=tkinter.HORIZONTAL, cursor="hand2")
		self.link_scrollbar.place(x=100, y=155, width=500, height=15)
		self.link_entry = tkinter.Entry(font=("Helvetica", 11), justify=tkinter.CENTER, insertbackground="white", xscrollcommand=self.link_scrollbar.set,
		                                foreground="white", disabledforeground="white",
		                                background="#B2861C", disabledbackground="#664C10",
		                                highlightthickness=2, highlightcolor="white", highlightbackground="white",
		                                borderwidth=0)
		self.link_scrollbar.config(command=self.link_entry.xview)
		self.link_entry.place(x=100, y=115, width=500, height=35)

		self.folder_title = tkinter.Label(self.root, text="Folder:", font=("Helvetica", 17, "bold"), bg="#ffc028", fg="#ffffff")
		self.folder_title.place(x=15, y=155, width=80, height=100)
		self.folder_scrollbar = tkinter.Scrollbar(self.root, orient=tkinter.HORIZONTAL, cursor="hand2")
		self.folder_scrollbar.place(x=100, y=227, width=500, height=15)
		self.folder_entry = tkinter.Entry(font=("Helvetica", 11), justify=tkinter.CENTER, insertbackground="white", xscrollcommand=self.folder_scrollbar.set,
		                                  foreground="white", disabledforeground="white",
		                                  background="#B2861C", disabledbackground="#664C10",
		                                  highlightthickness=2, highlightcolor="white", highlightbackground="white",
		                                  borderwidth=0)
		self.folder_scrollbar.config(command=self.folder_entry.xview)
		self.folder_entry.place(x=100, y=187, width=500, height=35)

		self.browse_button = tkinter.Label(self.root, text="Browse", font=("Helvetica", 11, "bold"),
		                                   bg="#B2861C", fg="#ffffff", activebackground="#664C10", activeforeground="#ffffff", cursor="hand2",
		                                   borderwidth=0, highlightthickness=2, highlightcolor="white", highlightbackground="white")
		self.browse_button.bind("<Button-1>", lambda event: self.browse())
		self.browse_button.place(x=610, y=187, width=80, height=35)

		self.download_button = tkinter.Label(self.root, text="Download", font=("Helvetica", 11, "bold"),
		                                     bg="#B2861C", fg="#ffffff", activebackground="#664C10", activeforeground="#ffffff", cursor="hand2",
		                                     borderwidth=0, highlightthickness=2, highlightcolor="white", highlightbackground="white")
		self.download_button.bind("<Button-1>", lambda event: self.download())
		self.download_button.place(x=610, y=115, width=80, height=35)

		self.hourglass_frames = [tkinter.PhotoImage(file=resource_path(f"data/hourglass-gif/frame_{i:02}.png")) for i in range(0, 29)]
		self.hourglass_active = False
		self.hourglass_frame_index = 0
		self.hourglass = tkinter.Label(self.root, image=self.hourglass_frames[0] if self.hourglass_active else "", bg="#ffc028")
		self.hourglass.place(x=600, y=20, width=75, height=75)

		self.images_switch_state = True
		self.images_switch = tkinter.Label(self.root, text="Images", font=("Helvetica", 11, "bold"),
		                                   bg="#664C10", fg="#ffffff", activebackground="#664C10", activeforeground="#ffffff", cursor="hand2",
		                                   borderwidth=0, highlightthickness=4, highlightcolor="green", highlightbackground="green")
		self.images_switch.bind("<Button-1>", lambda event: self.toggle_images())
		self.images_switch.place(x=260, y=255, width=80, height=35)

		self.videos_switch_state = True
		self.videos_switch = tkinter.Label(self.root, text="Videos", font=("Helvetica", 11, "bold"),
		                                   bg="#664C10", fg="#ffffff", activebackground="#664C10", activeforeground="#ffffff", cursor="hand2",
		                                   borderwidth=0, highlightthickness=4, highlightcolor="green", highlightbackground="green")
		self.videos_switch.bind("<Button-1>", lambda event: self.toggle_videos())
		self.videos_switch.place(x=360, y=255, width=80, height=35)

		self.download_thread = None

		self.root.mainloop()

		psutil.Process(os.getpid()).kill()

	def download(self):
		if self.hourglass_active:
			return

		inputed_link = self.link_entry.get()
		inputed_folder = self.folder_entry.get()

		if not os.path.isabs(inputed_folder):
			inputed_folder = os.path.join(os.path.dirname(sys.executable), inputed_folder)

		if not validators.url(inputed_link):
			tkinter.messagebox.showerror("Error!", "The specified link is invalid.")
			return

		if not os.path.isdir(inputed_folder):
			if tkinter.messagebox.askyesno("Error!", "The specified folder does not exist. Should it be created?"):
				try:
					os.mkdir(inputed_folder)
				except PermissionError:
					print(inputed_folder)
					tkinter.messagebox.showerror("Error!", "You do not have permission to create a folder in this location.")
					return
			else:
				return

		self.start_hourglass()
		self.download_button.config(background="#664C10", activebackground="#664C10", cursor="arrow", highlightcolor="#000000", highlightbackground="#000000")
		self.browse_button.config(background="#664C10", activebackground="#664C10", cursor="arrow", highlightcolor="#000000", highlightbackground="#000000")
		self.link_entry.config(state=tkinter.DISABLED, highlightcolor="#000000", highlightbackground="#000000")
		self.folder_entry.config(state=tkinter.DISABLED, highlightcolor="#000000", highlightbackground="#000000")
		self.images_switch.config(cursor="arrow")
		self.videos_switch.config(cursor="arrow")

		self.download_thread = threading.Thread(target=self.download_thread_function, args=(inputed_link, inputed_folder))
		self.download_thread.start()
		self.download_thread_check()

	def download_thread_function(self, inputed_link, inputed_folder):
		if self.images_switch_state:
			download_images(inputed_link, inputed_folder)
		if self.videos_switch_state:
			match platform.system():
				case "Windows":
					ffmpeg_path = resource_path("lib/ffmpeg/windows/ffmpeg.exe")
				case "Linux":
					ffmpeg_path = resource_path("lib/ffmpeg/linux/ffmpeg")
				case "Darwin":
					ffmpeg_path = resource_path("lib/ffmpeg/macos/ffmpeg")
				case _:
					ffmpeg_path = ""
			download_videos(inputed_link, inputed_folder, ffmpeg_path)

	def download_thread_check(self):
		if self.download_thread.is_alive():
			self.root.after(100, self.download_thread_check)
		else:
			self.stop_hourglass()
			self.download_button.config(background="#B2861C", activebackground="#664C10", cursor="hand2", highlightcolor="white", highlightbackground="white")
			self.browse_button.config(background="#B2861C", activebackground="#664C10", cursor="hand2", highlightcolor="white", highlightbackground="white")
			self.link_entry.config(state=tkinter.NORMAL, highlightcolor="white", highlightbackground="white")
			self.folder_entry.config(state=tkinter.NORMAL, highlightcolor="white", highlightbackground="white")
			self.images_switch.config(cursor="hand2")
			self.videos_switch.config(cursor="hand2")

	def browse(self):
		if self.hourglass_active:
			return

		result_folder = tkinter.filedialog.askdirectory(mustexist=True, initialdir=self.folder_entry.get() if os.path.isdir(self.folder_entry.get()) else os.path.dirname(sys.executable))
		if result_folder != "":
			self.folder_entry.delete(0, tkinter.END)
			self.folder_entry.insert(0, result_folder)

	def start_hourglass(self):
		self.hourglass_active = True
		self.hourglass_frame_index = -1
		self.spin_hourglass()

	def stop_hourglass(self):
		self.hourglass_active = False
		self.hourglass.config(image="")

	def spin_hourglass(self):
		if self.hourglass_active:
			self.hourglass_frame_index += 1
			self.hourglass_frame_index %= len(self.hourglass_frames)
			self.hourglass.config(image=self.hourglass_frames[self.hourglass_frame_index])
			self.root.after(50, self.spin_hourglass)

	def toggle_images(self):
		if self.hourglass_active:
			return

		self.images_switch_state = not self.images_switch_state
		self.images_switch.config(highlightcolor="green" if self.images_switch_state else "red", highlightbackground="green" if self.images_switch_state else "red",
		                          foreground="white" if self.images_switch_state else "black")

	def toggle_videos(self):
		if self.hourglass_active:
			return

		self.videos_switch_state = not self.videos_switch_state
		self.videos_switch.config(highlightcolor="green" if self.videos_switch_state else "red", highlightbackground="green" if self.videos_switch_state else "red",
		                          foreground="white" if self.videos_switch_state else "black")


if __name__ == "__main__":
	if platform.system() not in ["Windows", "Darwin", "Linux"]:
		tkinter.messagebox.showerror("Error!", "Your operating system is not supported.")
		sys.exit()

	App()
