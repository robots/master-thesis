
class symbol:
	_SYMBOLS = {}
	_UNK_SYMBOLS = []

	def get_unknown(self):
		if len(self._UNK_SYMBOLS) > 0:
			return self._UNK_SYMBOLS.pop()

		return False

	def add_unknown(self, syms):
		for s in syms:
			self._UNK_SYMBOLS.append(s)

	def add(self, sym, val):
		print "Added symbol '%s' = 0x%x" % (sym, val)
		self._SYMBOLS[sym] = val

	def get(self, sym):
		if self.exists(sym):
			return self._SYMBOLS[sym]

		raise "No such symbol"

	def exists(self, sym):
		return sym in self._SYMBOLS

