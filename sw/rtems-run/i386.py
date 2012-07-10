
from struct import pack, unpack
#import gca

def hexit( text ):
	h = []

	for c in text:
		h.append( "%02X" % (ord(c)) )
	return " ".join(h)


class i386:
	_gdb_regs = [
		('eax', 32),
		('ecx', 32),
		('edx', 32),
		('ebx', 32),
		('esp', 32),
		('ebp', 32),
		('esi', 32),
		('edi', 32),
		('eip', 32),
		('eflags', 32),
		('cs', 32),
		('ds', 32),
		('ss', 32),
		('es', 32),
		('fs', 32),
		('gs', 32),
		('fp0', 80),
		('fp1', 80),
		('fp2', 80),
		('fp3', 80),
		('fp4', 80),
		('fp5', 80),
		('fp6', 80),
		('fp7', 80),
		('fpuc', 32), # need correct names
		('fpus', 32),
		('ftag', 32),
		('fiseg', 32),
		('fioff', 32),
		('foseg', 32),
		('fooff', 32),
		('fop', 32),
		('xmm0', 128),
		('xmm1', 128),
		('xmm2', 128),
		('xmm3', 128),
		('xmm4', 128),
		('xmm5', 128),
		('xmm6', 128),
		('xmm7', 128),
		('mxcsr', 32),
	]

#	def __init__(self, cpu = False):
#		if cpu != False:
#			r = gca.target_regs_read(cpu)
#			self._regs = parse_gdb_regs(r)

	def _reg_data(self, name, reg, bits):
		b = (bits + 7) / 8

		if not name in reg:
			return '\x00' * b
		
		return reg[name]

	def _reg_parse(self, data, reg, bits):
		b = (bits + 7) / 8

		if len(data) != b:
			raise Exception("data size doesn't match")

		return data

	def print_regs(self, regs):
		for name, size in self._gdb_regs:
			print "%s(%d) = %s" % (name, size, hexit(self._reg_data(name, regs, size)))

	def parse_gdb_regs(self, data):
		regs = {}

		for name, size in self._gdb_regs:
			b = (size + 7) / 8

			if len(data) < b:
				break

			regs[name] = self._reg_parse(data[:b], name, size)
			data = data[b:]

		self._regs = regs
		return regs

	def get_gdb_regs(self, regs):
		out = []

		for name, size in self._gdb_regs:
			out.append(self._reg_data(name, regs, size))

		return ''.join(out)

	def get_reg(self, name):
		# TODO: check reg is 32bit
		return unpack("I", self._regs[name])[0]

	def set_reg(self, name, value):
		# TODO: check reg is 32bit
		self._regs[name] = pack("I", value)

