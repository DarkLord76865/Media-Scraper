import cv2
import os

for img in os.listdir('..\\data\\hourglass-gif'):
	image = cv2.imread(f'..\\data\\hourglass-gif/{img}')
	image = cv2.resize(image, (75, 75), interpolation=cv2. INTER_AREA)
	cv2.imwrite(f'..\\data\\hourglass-gif/{img}', image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
