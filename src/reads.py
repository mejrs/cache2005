import struct

_UByte = struct.Struct(">B")
def readUByte(f):
	return _UByte.unpack(f.read(1))[0]

_Byte = struct.Struct(">b")
def readByte(f):
	return _Byte.unpack(f.read(1))[0]

def readBytes(f, n):
	return [val for val, in _UByte.iter_unpack(f.read(n))]

_UShort = struct.Struct(">H")
def readUShort(f):
	return _UShort.unpack(f.read(2))[0]

_Short = struct.Struct(">h")
def readShort(f):
	return _Short.unpack(f.read(2))[0]


def readSequence(f):
	count = readUShort(f)
	return [val for val, in _UShort.iter_unpack(f.read(3*count))]

def readSmallSequence(f):
	count = readUShort(f)
	return [val for val, in _UShort.iter_unpack(f.read(2*count))]

def readSequence1(f):
	count = readUShort(f)
	return [val for val, in _UShort.iter_unpack(f.read(1*count))]

_UInt = struct.Struct(">I")
def read4UByte(f):
	return _UInt.unpack(f.read(4))[0]

def read3UByte(f):
	return (readUByte(f) << 16) | (readUByte(f) << 8) | readUByte(f)

_Int = struct.Struct(">i")
def readSignedInt(f):
	return _Int.unpack(f.read(4))[0]


def readCoordinate(f):
	loc, = _Int.unpack(f.read(4))
	plane = loc >> 28
	x = (loc >> 14) & 0x3FFF
	y = loc & 0x3FFF
	return dict(zip(("plane", "x", "y"), (plane, x, y)))

def readInt(f):
	return _Int.unpack(f.read(4))[0] & 0x7FFFFFFF

def read3ByteInt(f):
	unsigned = (readUByte(f) << 16) | (readUByte(f) << 8) | readUByte(f)
	return unsigned & 0x7FFFFFFF

def read3ByteIntSwap(f):
	unsigned = (readUByte(f)) | (readUByte(f) << 8) | (readUByte(f) << 16)
	return unsigned & 0x7FFFFFFF

def readBigSmart(f):
	return readUShort(f) if f.tell() >= 0 else readInt(f)

_ULong = struct.Struct(">Q")
def readLong(f):
	return _ULong.unpack(f.read(8))[0] & 0x7FFFFFFFFFFFFFFF

def readUSmart(f):
	i = readUByte(f)
	if i >= 128:
		i -= 128
		return i << 8 | readUByte(f)
	else:
		return i

def readDecrSmart(f):
	first = readUByte(f)
	if first < 128:
		return first - 1
	return ((first << 8) | readByte(f)) - 32769

def readSmart(f):
	first = readUByte(f)
	if first < 128:
		return first - 64
	return ((first << 8) | readUByte(f)) - 49152

def readSmart32(f):
	i = readUByte(f)
	f.seek(f.tell()-1)
	if i >= 128:
		return readInt(f)
	value = readUShort(f)
	if value == 32767:
		return -1
	return value

def readSmarts(f):
	value = 0
	offset = readUSmart(f)
	while offset == 32767:
		offset = readUSmart(f)
		value += 32767
	value += offset
	return value

def readChar(f):
	return chr(readUByte(f))

def returnTrue(f):
	return True

def returnFalse(f):
	return False

def readString(f):
	string = ""
	while (c := readUByte(f)) != 0:
		string += chr(c)
	return string

def readPaddedString(f):
	readUByte(f)
	return readString(f)

_AmbientSound = struct.Struct(">HHHHB")
def readAmbientSound(f):
	return _AmbientSound.unpack(f.read(9))




def readMaskedIndex(f):
	number =  readUShort(f)

	# TODO
	# default byte[] readMaskedIndex() throws IOException {
	#     int number = this.readUShort();
	#     int count = 0;
	#     for(int c=number; c > 0; c >>= 1)
	#         count++;
	#     int value = 0;
	#     byte[] result = new byte[count];

	#     for(int i=0; i < count; i++){
	#         if((number&(0x01<<i)) > 0)
	#             result[i] = (byte) value++;
	#         else
	#             result[i] = -1;
	#     }
	#     return result;
	return number

# a.k.a. Gaz' rep
def readReplace(f, readType, replacementTarget, replacement):
	return replacement if (value := readType(f)) == replacementTarget else value

def readMorphTable(f, withlast = False):
	table = {}
	table['varbit'] = readReplace(f, readUShort, 0xFFFF, -1)
	table['varp'] = readReplace(f, readUShort, 0xFFFF, -1)

	last = readReplace(f, readUShort, 0xFFFF, -1) if withlast else -1

	count = readUSmart(f)

	table['ids'] = [val if val != 0xFFFF else -1 for val, in _UShort.iter_unpack(f.read(2*(count+1)))]
	table['ids'].append(last)
	return table

def readExtendedMorphTable(f):
	return readMorphTable(f, withlast = True)

def readSequence13(f):
	ret = []
	count = readUShort(f)
	for i in range(count):
		inner_count = readUByte(f)
		if inner_count == 0:
			ret.append([])
		else:
			ret.append([val for val, in _UByte.iter_unpack(f.read(inner_count*2 + 1))])
	return ret

def readObjectMorphTable(f, withlast = False):
	table = {}
	table['varbit'] = readReplace(f, readUShort, 65535, -1)
	table['varp'] = readReplace(f, readUShort, 65535, -1)

	last = readSmart32(f) if withlast else -1

	count = readUSmart(f)
	table['ids'] = [readSmart32(f) for _ in range(count+1)]
	if withlast:
		table['ids'].append(last)
	return table

# the actual difference between this and readObjectExtendedMorphTable is that one defines a morph with a -1 default state while the other has a visible default state
def readObjectExtendedMorphTable(f):
	return readObjectMorphTable(f, withlast = True)

def readBitMaskedData(f):
	result = []
	mask = readUByte(f)
	while mask > 0:
		if mask & 0x1 == 1:
			result.append([readSmart32(f), readDecrSmart(f)])
		else:
			result.append([-1, -1])
		mask = mask // 2
	return result

reads = globals()
def read(name):
	if type(name) == int:
		return lambda f: readBytes(f, name)
	elif name in reads:
		return reads[name]
	else:
		raise ValueError('%s not found' % name)

def readTable(f):
	table = {}
	count = readUByte(f)

	for _ in range(count):
		isString = readUByte(f) == 1
		_key = read3UByte(f)
		key = _rename.get(_key, _key)
		key = key if key != _key else "extra_" + hex(_key).upper()[2:].zfill(6)
		value = readString(f) if isString else readInt(f)
		table[key] = value

	return table
