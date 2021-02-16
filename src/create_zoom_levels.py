from PIL import Image, ImageDraw
import math
import os
from pathlib import Path
import multiprocessing as mp
import functools as ft
import itertools as it
import re

img_size = 256
quarter_img_size = 128

def create(filename_format, backfill, zoom, available_tiles, plane, x , y):
	im = Image.new("RGBA", (img_size,img_size), backfill)

	for i, j in it.product(range(2), range(2)):
		if (plane, 2*x+i, 2*y+j) in available_tiles:
			insert_im = Image.open(filename_format % (zoom+1, plane,  2*x+i, 2*y+j))
			insert_im = insert_im.resize((quarter_img_size, quarter_img_size), Image.ANTIALIAS)
			im.paste(insert_im, (quarter_img_size*i, quarter_img_size*(1-j)))

	im.save(filename_format % (zoom, plane,  x, y), "PNG")


def main(directory, init_zoom = None, min_zoom = -4, backfill = (0,0,0)):
	if init_zoom == None:
		#looking at directory to determine this..
		init_zoom = max(map(int, os.listdir(directory)))

	run_for_zoom(directory, init_zoom, min_zoom, backfill)

def run_for_zoom(directory, zoom, min_zoom, backfill):
	if zoom > min_zoom:
		try:
			os.makedirs(directory + "/" + str(zoom - 1))
		except FileExistsError:
			pass

		tiles = os.listdir(directory + "/" + str(zoom))
		if len(tiles) == 0:
			raise FileNotFoundError('No tiles found in directory %s/%d' % (directory, zoom))

		current_tiles = set(map(lambda tile: tuple(map(int, re.findall("\d+", tile))), tiles))
		next_tiles = map(lambda c: (c[0], c[1] >> 1, c[2] >> 1), current_tiles)

		func = ft.partial(create, directory + "/%d/%d_%d_%d.png", backfill, zoom - 1, current_tiles)

		# Do not use multiprocessing if this module was invoked by a child process (i.e. already a multiprocessing process)
		if mp.current_process().name == 'MainProcess':
			pool = mp.Pool(mp.cpu_count())
			pool.starmap(func, next_tiles)
			pool.close()
			pool.join()
		else:
			for tile in next_tiles:
				func(*tile)

		#recursive invocation for next zoom level
		run_for_zoom(directory, zoom - 1, min_zoom, backfill)

if __name__ == "__main__":
	main("C:/Users/bruno/runescape/cache/out/exports/private_osrsmap/map_squares_osrs/-1", backfill = (0, 0, 0, 0))
