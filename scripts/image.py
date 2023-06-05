import os
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
import requests


IMG_EXT = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp']
REQ_HEAD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0"}
HTML_PARSER = 'html.parser'  # default that comes with python


def download_images(website, save_folder) -> bool:
	"""
	Downloads all images from given website and saves them to given folder.
	:param website: Website to download images from.
	:param save_folder: Folder to save images to.
	:return: None
	"""

	# download and parse website
	response = requests.get(website, headers=REQ_HEAD)
	if response.status_code != 200:
		return False
	parsed_page = BeautifulSoup(response.text, HTML_PARSER)

	# get all images from website (embedded and linked)
	images = []
	for img in parsed_page.find_all('img'):
		try:  # Skip images with empty 'src' attribute
			if img['src'].split('?')[0].split('.')[-1] in IMG_EXT:
				images.append(urljoin(website, img['src']))
		except KeyError:
			pass
	for link in parsed_page.find_all('a'):
		try:  # Skip links with empty 'href' attribute
			if link['href'].split('?')[0].split('.')[-1] in IMG_EXT:
				images.append(urljoin(website, link['href']))
		except KeyError:
			pass
	images = list(set(images))  # Remove duplicates

	# create save folder if it doesn't exist
	if not os.path.isdir(save_folder):
		os.mkdir(save_folder)

	# download images
	for image in images:
		# download image
		downloaded_image_resp = requests.get(image, headers=REQ_HEAD)
		if downloaded_image_resp.status_code != 200:
			continue
		downloaded_image = downloaded_image_resp.content

		# get image name and path
		filename = image.split('?')[0].split('/')[-1]
		filename = filename.strip()
		filename = sanitize_filename(filename)
		file_system_path = os.path.join(save_folder, filename)
		if os.path.isfile(file_system_path):
			with open(file_system_path, "rb") as opened_file:
				# skip if image with same name and content already exists
				if downloaded_image == opened_file.read():
					continue

			# if image with same name already exists, add number to filename
			current_file_number = 1
			while os.path.isfile(file_system_path):
				current_file_number += 1
				filename = os.path.splitext(filename)[0] + f" ({current_file_number})" + os.path.splitext(filename)[1]
				file_system_path = os.path.join(save_folder, filename)

		# save image
		with open(file_system_path, 'wb') as new_file:
			new_file.write(downloaded_image)

	return True


if __name__ == '__main__':
	download_images('https://www.google.com/', 'images')
