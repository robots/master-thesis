
from struct import pack, unpack
import gca

def hexit( text ):
	h = []
	for c in text:
		h.append( "%02X" % (ord(c)) )
	return " ".join(h)

OBJECTS_APIS = ["NO_API", "INTERNAL_API",	"CLASSIC_API",	"POSIX_API", "ITRON_API"]

OI_TAB = "_Objects_Information_table"

UnknownSymbols = [
	OI_TAB,
	"_Thread_Executing"
]

Symbols = []
threads = []
thread_list = []

def rtems_get_objectinfo_table(cpu):
	if not symbol_exists(OI_TAB):
		return []
	
	addr = symbol_get(OI_TAB)
	data = gca.target_memory_read(cpu, addr, 4 * len(OBJECTS_APIS))
	info_ptrs = []
	while len(data) >= 4:
		ptr = unpack("I", data[:4])[0]
		info_ptrs.append(ptr)
		data = data[4:]

	return info_ptrs

def rtems_get_objectinfo_content(cpu, addr):
	data = gca.target_memory_read(cpu, addr, 64)

	api = unpack("I", data[:4])[0]
	clas = unpack("H", data[4:6])[0]
	maximum = unpack("H", data[16:18])[0]
#	allocation_size = unpack("H", data[22:24])[0]
#	size = unpack("I", data[24:28])[0]
	local_table = unpack("I", data[28:32])[0]
	out = {"api": api, "class": clas, "maximum": maximum, "local_table": local_table}
	print out
	return out

def rtems_get_threadcontrol(cpu, addr):
#TODO: parse registers (ESP, EBP, ...)
	data = gca.target_memory_read(cpu, addr, 5*4+4)
#	print repr(data)
	tc = unpack("IIIIII", data)
	out = {"oid": tc[2], "name": data[15:11:-1], "current_state": tc[4]}
#	print out
	return out

def rtems_get_current(cpu):
	thread_ctrl_ptr = symbol_get("_Thread_Executing")
	if thread_ctrl_ptr == False:
		return 1

	thread_control = rtems_get_threadcontrol(cpu, thread_ctrl_ptr)
	print "curent " , thread_control
	return thread_control["oid"]		

def rtems_get_threads(cpu):
	thread_list = []

	ptrs = rtems_get_objectinfo_table(cpu)
	for i in range(1, len(OBJECTS_APIS)):
#	print "Parsing API: %s" % OBJECTS_APIS[i]
		if ptrs[i] == 0:
			continue

		oi_ptr = gca.target_memory_read(cpu, ptrs[i] + 4, 4) # +4 to get TASKS
		oi = rtems_get_objectinfo_content(cpu, unpack("I", oi_ptr)[0])

		for i in range(1, oi["maximum"]+1):
			data = gca.target_memory_read(cpu, oi["local_table"] + i * 4 , 4)
			thread_ctrl_ptr = unpack("I", data)[0]
#			print "TC ptr = %x" % thread_ctrl_ptr

			thread_control = rtems_get_threadcontrol(cpu, thread_ctrl_ptr)
#			print thread_control
			if thread_control["current_state"] & 1 == 0: # filter dormant threads
				thread_list.append(thread_control)

	return thread_list	

def thread_regs_read(cpu, tid):
	regs = gca.target_regs_read(cpu)
	return regs

def thread_regs_write(cpu, tid, regs):
	ret = gca.target_regs_write(cpu, regs)
	if ret > 0:
		return True
	return False

def thread_mem_read(cpu, tid, addr, length):
#	if (thread_getcurrent(cpu) != tid) 
	return gca.target_memory_read(cpu, addr, length)

def thread_mem_write(cpu, tid, addr, data):
#	if (thread_getcurrent(cpu) != tid) 
	ret = gca.target_memory_write(cpu, addr, data)
	if ret > 0:
		return True;
	return False

def threadlist_create(cpu):
	global threads
	global thread_list

	threads = []
	thread_list = []

	thread_list = rtems_get_threads(cpu)

	for i in range(0, len(thread_list)):
		t = thread_list[i]
		threads.append(t["oid"])
				
	return 1

def threadlist_count(cpu):
	return len(threads)

def threadlist_getnext(cpu):
	global threads
	out = 0
	if len(threads) > 0:
		out = threads.pop()
	return out

def thread_isalive(cpu, t_id):
	threadlist_create(cpu)

	for i in range(0, len(thread_list)):
		t = thread_list[i]
		if t["oid"] == t_id:
			return True

	return False

def thread_getcurrent(cpu):
	return rtems_get_current(cpu)

def thread_getinfo(cpu, t_id):
	s = "%x" % (t_id)
	for i in range(0, len(thread_list)):
		t = thread_list[i]
		if t["oid"] == t_id:
			s = "%s %04x" % (t["name"], t["current_state"] & 0xffff)
			break;

	return s

def symbol_getunknown():
	global UnknownSymbols
	out = ""
	if len(UnknownSymbols) > 0:
		out = UnknownSymbols.pop()

	return out

def symbol_add(symbol, value):
	global Symbols

	print "Added symbol '%s' = 0x%x" % (symbol, value)
	Symbols.append((symbol, value))

def symbol_get(symbol):
	for s, addr in Symbols:
		if s == symbol:
			return addr

	return False

def symbol_exists(symbol):
	for s, addr in Symbols:
		if s == symbol:
			return True

	return False

