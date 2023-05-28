import copy
import io
import os
import shutil
import subprocess
import sys

from yt_dlp import YoutubeDL


def download_videos(website, save_folder, ffmpeg_path):

	if not os.path.isdir(save_folder):
		os.mkdir(save_folder)

	with YoutubeDL() as ydl:
		info_dict = ydl.extract_info(website, download=False)

	if "entries" in info_dict.keys():
		for entry_ind in range(len(info_dict["entries"])):
			process_video(website, save_folder, copy.deepcopy(info_dict["entries"][entry_ind]), entry_ind + 1)
	else:
		process_video(website, save_folder, copy.deepcopy(info_dict), ffmpeg_path)

def process_video(website, save_folder, info, ffmpeg_path, playlist_index=None) -> bool:
	# get video title
	try:
		video_title = info["title"]
	except KeyError:
		return False

	# find the best video format

	# copy the list of available formats to avoid modifying the original list
	try:
		available_formats = copy.deepcopy(info["formats"][::-1])
		# formats are sorted worst to best, so we reverse the list to get the best first
	except KeyError:
		return False

	# remove formats without video
	deleted = 0
	for fmt_ind in range(len(available_formats)):
		try:
			if available_formats[fmt_ind - deleted]["vcodec"] == "none":
				available_formats.pop(fmt_ind - deleted)
				deleted += 1
		except KeyError:
			pass

	# find video with the highest resolution
	max_width = 0
	for fmt in available_formats:
		try:
			curr_width = fmt["width"]
			if curr_width > max_width:
				max_width = curr_width
		except KeyError:
			pass
	if max_width == 0:
		return False

	# remove formats with lower resolution
	deleted = 0
	for fmt_ind in range(len(available_formats)):
		try:
			if available_formats[fmt_ind - deleted]["width"] != max_width:
				available_formats.pop(fmt_ind - deleted)
				deleted += 1
		except KeyError:
			available_formats.pop(fmt_ind - deleted)
			deleted += 1

	# find video with the biggest file size (highest quality)
	max_size = 0
	for fmt in available_formats:
		try:
			if fmt["filesize"] > max_size:
				max_size = fmt["filesize"]
		except KeyError:
			try:
				if fmt["filesize_approx"] > max_size:
					max_size = fmt["filesize_approx"]
			except KeyError:
				pass
	if max_size == 0:
		return False

	# remove formats with lower quality
	deleted = 0
	for fmt_ind in range(len(available_formats)):
		try:
			if available_formats[fmt_ind - deleted]["filesize"] < max_size * 0.95:
				available_formats.pop(fmt_ind - deleted)
				deleted += 1
		except KeyError:
			try:
				if available_formats[fmt_ind - deleted]["filesize_approx"] < max_size * 0.95:
					available_formats.pop(fmt_ind - deleted)
					deleted += 1
			except KeyError:
				available_formats.pop(fmt_ind - deleted)
				deleted += 1

	# store the id of the best video format
	best_video = available_formats[0]["format_id"]

	# find the best audio format

	# copy the list of available formats to avoid modifying the original list
	try:
		available_formats = copy.deepcopy(info["formats"][::-1])
		# formats are sorted worst to best, so we reverse the list to get the best first
	except KeyError:
		return False

	# remove formats without audio
	deleted = 0
	for fmt_ind in range(len(available_formats)):
		try:
			if available_formats[fmt_ind - deleted]["vcodec"] != "none":
				available_formats.pop(fmt_ind - deleted)
				deleted += 1
		except KeyError:
			available_formats.pop(fmt_ind - deleted)
			deleted += 1

	if len(available_formats) == 0:
		# if there is no audio only format, assume the best video format has audio
		best_audio = best_video
	else:
		# find audio with the biggest file size (highest quality)
		max_size = 0
		for fmt in available_formats:
			try:
				if fmt["filesize"] > max_size:
					max_size = fmt["filesize"]
			except KeyError:
				try:
					if fmt["filesize_approx"] > max_size:
						max_size = fmt["filesize_approx"]
				except KeyError:
					pass
		if max_size == 0:
			return False

		# remove formats with lower quality
		deleted = 0
		for fmt_ind in range(len(available_formats)):
			try:
				if available_formats[fmt_ind - deleted]["filesize"] < max_size * 0.95:
					available_formats.pop(fmt_ind - deleted)
					deleted += 1
			except KeyError:
				try:
					if available_formats[fmt_ind - deleted]["filesize_approx"] < max_size * 0.95:
						available_formats.pop(fmt_ind - deleted)
						deleted += 1
				except KeyError:
					available_formats.pop(fmt_ind - deleted)
					deleted += 1

		# store the id of the best audio format
		best_audio = available_formats[0]["format_id"]

	# here we have the best video and audio formats (their ids), and the video title

	# download video
	# redirect stdout to capture the output file name
	old_stdout = sys.stdout
	new_stdout = io.StringIO()
	sys.stdout = new_stdout
	ydl_opts = {
		'format': best_video,
		'outtmpl': '%(id)s.%(ext)s',
		'overwrites': True,
	}
	if playlist_index is not None:
		ydl_opts['playlist_items'] = str(playlist_index)
	with YoutubeDL(ydl_opts) as ydl:
		ydl.download([website])
	sys.stdout = old_stdout
	video_info = new_stdout.getvalue()
	video_file = None
	for line in video_info.split("\n"):
		if "Destination: " in line:
			video_file = line.split("Destination: ")[1].rstrip("\n")
	if video_file is None:
		return False
	os.rename(video_file, f"media_scraper_video_{video_file}")
	video_file = f"media_scraper_video_{video_file}"

	if best_video != best_audio:
		# download audio
		# redirect stdout to capture the output file name
		old_stdout = sys.stdout
		new_stdout = io.StringIO()
		sys.stdout = new_stdout
		ydl_opts = {
			'format': best_audio,
			'outtmpl': '%(id)s.%(ext)s',
			'overwrites': True,
		}
		if playlist_index is not None:
			ydl_opts['playlist_items'] = str(playlist_index)
		with YoutubeDL(ydl_opts) as ydl:
			ydl.download([website])
		sys.stdout = old_stdout
		audio_info = new_stdout.getvalue()
		audio_file = None
		for line in audio_info.split("\n"):
			if "Destination: " in line:
				audio_file = line.split("Destination: ")[1].rstrip("\n")
		if audio_file is None:
			return False
		os.rename(audio_file, f"media_scraper_audio_{audio_file}")
		audio_file = f"media_scraper_audio_{audio_file}"
	else:
		audio_file = video_file

	# here we have the video and audio files downloaded

	if best_audio == best_video:
		# rename file to avoid ffmpeg overwriting

		# remux with ffmpeg
		subprocess.call([ffmpeg_path, '-y', '-i', video_file, '-c', 'copy', video_title + '.mp4'])

		os.remove(video_file)
	else:
		# rename files to avoid ffmpeg overwriting

		# merge with ffmpeg
		subprocess.call([ffmpeg_path, '-y', '-an', '-i', video_file, '-vn', '-i', audio_file, '-c', 'copy', video_title + '.mp4'])

		os.remove(video_file)
		os.remove(audio_file)

	shutil.move(video_title + '.mp4', os.path.join(save_folder, video_title + '.mp4'))

	return True


if __name__ == "__main__":
	download_videos('https://www.youtube.com/playlist?list=PLpQrothfTflafHmcY_EBwpFBVsKfpATOe', "videos", ffmpeg_path="../lib/ffmpeg/bin/ffmpeg.exe")
