import struct, itertools, os, csv

from config import base
from reads import *



def get_info():
	info = {}
	with open(base + "/data/map_info.csv",) as csv_file:
	   data = csv.reader(csv_file)
	   next(data)
	   for row in data:
		   file = f"{base}/data/mapsquares/{row[0]}.dat"
		   key = int(row[1])
		   ty = row[2]
		   info[(key, ty)] = file

	return info


class Mapsquare:
	__slots__ = ['coords', 'tiles', 'objects']

	INFO = get_info()

	def __init__(self, i,j):
		self.coords = (i,j)

		floor_file = self.INFO[(i*256 + j, 'Floor')]
		with open(floor_file, mode = 'rb') as floor_data:
			self.tiles = self._decodeSquares(floor_data)

		obj_file = self.INFO[(i*256 + j, 'Objects')]
		with open(obj_file, mode = 'rb') as obj_data:
			self.objects = self._decodeObjects(i, j, obj_data)

	@staticmethod
	def _decodeObjects(i, j, file):
		objectId = -1
		objectLocations = []
		while (objIncr := readSmarts(file)) != 0:
			objectId += objIncr
			location = 0
			while (locIncr := readUSmart(file) ) != 0:
				objectData = readUByte(file)
				thing = {}
				location += locIncr - 1
				thing['id'] = objectId
				thing['x'] = i << 6 | (location >> 6) & 0x3F
				thing['y'] = j << 6 | location & 0x3F
				thing['plane'] = location >> 12
				thing['type'] = (objectData >> 2) & 0x1F
				thing['rotation'] = objectData & 0x3
				objectLocations.append(thing)
		assert (remainder := file.read()) == b'', f"file was not exhausted: {remainder}"
		return objectLocations


	@staticmethod
	def _decodeSquares(file, nplanes=4):
		squares = {}

		for plane, x, y in itertools.product(range(nplanes), range(64), range(64)):
			tile = {}
			while attribute := readUByte(file):
				if attribute == 1:
					tile["height"] = readUByte(file)
					break
				elif attribute <= 49:
					tile["attrOpCode"] = attribute
					tile["overlayId"] = readUByte(file)
					tile["overlayPath"] = (attribute -2)//4
					tile["overlayRotation"] = (attribute -2) & 3
				# probably wrong
				elif attribute <= 81:
					tile["settings"] = attribute - 49
					tile["underlayId"] = attribute - 81

			squares[(plane,x,y)] = tile

		assert (remainder := file.read()) == b'', f"file was not exhausted: {remainder}"

		return squares


if __name__ == "__main__":
	for i, j in itertools.product(range(100), range(200)):
		try:
			sq = Mapsquare(i, j)
			for obj in sq.objects:
				if obj["id"] == 820:
					print(obj)

		except (KeyError, FileNotFoundError):
			pass
