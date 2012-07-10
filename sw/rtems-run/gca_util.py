
import gca
from struct import pack, unpack, calcsize

def unpack_int(data):
	return unpack("I", data)[0]

# dereferences pointer into integer/pointer
def deref_ptr(cpu, ptr, t = "I"):
	size = calcsize(t)
	ptr_data = gca.target_memory_read(cpu, ptr, size)
	data = unpack(t, ptr_data)[0]

	return data

def read_table(cpu, ptr, cnt, payload_type = "I"):
	table = []

	payload_size = calcsize(payload_type)
	for i in range(0, cnt):
		raw = gca.target_memory_read(cpu, ptr + i * payload_size, payload_size)
		data = unpack(payload_type, raw)

		if len(data) == 1:
			data = data[0]

		table.append(data)

	return table

# TODO:
# - add "next" ptr offset
def read_linkedlist(cpu, ptr, payload_type = "I"):
	table = []

	payload_size = calcsize(payload_type)

	addr = ptr
	while addr > 0:
		raw = gca.target_memory_read(cpu, addr, 4 + payload_size)
		addr = unpack_int(raw[:4])
		payload = unpack(payload_type, raw[4:])

		if len(payload) == 1:
			payload = payload[0]

		table.append(payload)

	return table

#kinda like repr, but better :-)
def hexit( text ):
	h = []

	for c in text:
		h.append("%02X" % (ord(c)))

	return " ".join(h)

