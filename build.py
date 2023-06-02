import os
import platform
import random
import shutil
import sys

import PyInstaller.__main__


def build(name, console, onefile, uac_admin, icon, upx, files, folders):
	work_path = "build"
	while os.path.isdir(work_path):
		work_path = f"build_{random.randint(1, 1_000_000_000)}"
	work_path = os.path.join(os.path.abspath("."), work_path)

	result_path = os.path.abspath(".")

	if os.path.isfile(os.path.join(os.path.abspath("."), f"{name}.exe")):
		os.remove(os.path.join(os.path.abspath("."), f"{name}.exe"))

	run_list = ['main.py',
	            '--noconfirm',
	            '--clean',
	            '--name', f"{name}",
	            '--workpath', work_path,
	            '--specpath', work_path,
	            '--distpath', result_path]

	if console:
		run_list.append("--console")
	else:
		run_list.append("--noconsole")

	if onefile:
		run_list.append("--onefile")
	else:
		run_list.append("--onedir")

	if uac_admin:
		run_list.append("--uac-admin")

	if icon != "":
		icon_path = os.path.join(os.path.abspath("."), icon)
		if not os.path.isfile(icon_path):
			raise Exception("Invalid icon!")
		else:
			run_list.extend(('--icon', icon_path))

	if upx != "":
		if not os.path.isfile(upx):
			raise Exception("Invalid UPX!")
		else:
			upx_path = os.path.join(os.path.abspath("."), os.path.dirname(upx))
			run_list.extend(('--upx-dir', upx_path))

	match platform.system():
		case "Windows":
			file_separator = ";"
		case "Linux":
			file_separator = ":"
		case "Darwin":
			file_separator = ":"
		case _:
			file_separator = ";"

	for file in files:
		if os.path.isfile(os.path.join(os.path.abspath("."), file)):
			run_list.extend(('--add-data', f'{os.path.join(os.path.abspath("."), file)}{file_separator}{os.path.dirname(file)}'))
		else:
			raise Exception("Invalid file!")

	for folder in folders:
		if os.path.isdir(folder):
			for walk in os.walk(folder, followlinks=False):
				for file in walk[2]:
					if os.path.isfile(os.path.join(walk[0], file)):
						run_list.extend(('--add-data', f'{os.path.join(os.path.abspath("."), os.path.join(walk[0], file))}{file_separator}{os.path.dirname(os.path.join(walk[0], file))}'))
					else:
						raise Exception("Invalid folder!")
		else:
			raise Exception("Invalid folder!")

	PyInstaller.__main__.run(run_list)
	shutil.rmtree(path=work_path, ignore_errors=True)

def main():
	name = "Media-Scraper"
	version = "1.0.2"

	name = f"{name}-v{version}"

	console = False
	onefile = True
	uac_admin = False

	files = []
	folders = []

	match platform.system():
		case "Windows":
			icon = "data/download_icon.ico"
			upx = "lib/upx/windows/upx.exe"

			files.append("lib/ffmpeg/windows/ffmpeg.exe")
		case "Linux":
			icon = ""
			upx = "lib/upx/linux/upx"

			files.append("lib/ffmpeg/linux/ffmpeg")
		case "Darwin":
			icon = "data/download_icon_mac.icns"
			upx = ""

			files.append("lib/ffmpeg/macos/ffmpeg")
		case _:
			print("Unknown platform!", file=sys.stderr)
			sys.exit(1)

	folders.append("data")

	if len(sys.argv) > 1 and sys.argv[1] == "--version":
		print(version)
	else:
		build(name, console, onefile, uac_admin, icon, upx, files, folders)


if __name__ == '__main__':
	main()
