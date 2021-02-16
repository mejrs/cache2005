from PIL import Image, ImageDraw
import itertools as it
import multiprocessing as mp
from functools import partial

from core import Mapsquare
import os
import create_zoom_levels

def render_chunk(p,i,j,filename_format):
	try:
		square = Mapsquare(i,j)
	except (KeyError, FileNotFoundError):
		return
	else:

		tile = Image.new('RGBA', (256, 256), (0,0,0,0))
		for x in range(64):
			for y in range(64):
				if height := square.tiles[(p,x,y)].get('height', 0):
					height_square = Image.new('RGBA', (4, 4), (255, 255, 0, height))
					tile.paste(height_square, (4 * x , 256 - 4 - 4 * y))

		if tile.getcolors() != [(64*64, (0, 0, 0, 0))]:
			tile.save(filename_format % (2,p,i,j),'PNG')

def main(MAP_FOLDER, enable_mp = True):
	filename_format = MAP_FOLDER + "/height/-1/%d/%d_%d_%d.png"

	try:
		os.makedirs(MAP_FOLDER + "/height/-1/2")
	except FileExistsError:
		pass

	iterator = it.product(range(4), range(100), range(200))

	func = partial(render_chunk, filename_format = filename_format)

	if enable_mp:
		pool = mp.Pool(mp.cpu_count())
		results = pool.starmap(func, iterator)
		pool.close()
		pool.join()
	else:
		for i in iterator:
			func(*i)

	create_zoom_levels.main(MAP_FOLDER + "/height/-1", backfill = (0,0,0,0))



if __name__ == "__main__":
	from config import base
	main(MAP_FOLDER = base, enable_mp = False)
