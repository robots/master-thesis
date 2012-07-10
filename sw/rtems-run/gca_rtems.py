
from struct import pack, unpack, calcsize
import gca
from gca_util import *
from gca_symbol import *
from rtems import *
from i386 import *


threads = []
thread_list = {}

symbol_storage = symbol()
target_cpu = i386()
target_os = rtems(symbol_storage, target_cpu)

# pointer to the QEMU's first cpu structure (so we can call gca methods)
first_cpu = 0

# this is the thread, user wants to debug
target_tid = 0

breakpoint = False

# this is a hook function on the break/watchpoints
# parameter is the "trapped" cpu
# return:
#  0 - default behaviour, trap passed to gdb
#  1 - target thread reached
#  2 - silent the trap, and continue to next breakpoint
#  3 - same as 2, but single-step
def hook_signal_trap(cpu):
	global target_tid
	global breakpoint

	if breakpoint == False:
		return 0

	# need to check that thread exists
	if not thread_isalive(cpu, target_tid):
		gca.monitor_output("Thread %08x no longer exists" % target_tid)
		breakpoint_cleanup()
		return 0

	# user doesn't care about other threads 
	if target_os.get_current_thread(cpu) != target_tid:
		return 2

	gca.monitor_output("Cink - Your thread is ready!")
	breakpoint_cleanup()

	return 1

def breakpoint_cleanup():
	global target_tid
	global breakpoint

	if not breakpoint == False:
		gca.breakpoint_remove(*breakpoint)
		breakpoint = False

	target_tid = 0

def thread_settarget(cpu, tid):
	global target_tid
	global breakpoint

	gca.monitor_output("set target = %08x" % tid)

	if not thread_isalive(cpu, tid):
		print "not alive"
		return False

	if thread_getcurrent(cpu) == tid:
		return False

	if not breakpoint == False:
		breakpoint_cleanup()

	# ebp is a "framepointer"
	fp = unpack_int(thread_list[tid]["registers"]["ebp"])

	# read the backtrace
	backtrace = read_linkedlist(cpu, fp)
	gca.monitor_output("backtrace is " + str(backtrace))

	# when thread is in context switch backtrace looks like:
	#
	# #0  0x00114756 in _Thread_Dispatch ()
	# #1  0x001113a1 in _Thread_Enable_dispatch ()
	# #2  0x0011140c in rtems_task_wake_after ()
	# #3  0x0010037e in Task_Relative_Period (unused=3) at tasks.c:167
	# #4  0x0011e4c3 in _Thread_Handler ()
	# #5  0x85b45d8b in ?? ()
	#
	# #0 is the actual EIP, and not contained in the backtrace
	#
	# 1st position will trigger breakpoint on each context switch,
	# which is probably safer, but a lot slower
	#
	# Note: This will only work then context switch called without interrupts.
	#
	# index - where
	# 2     - breakpoint in user program
	# 1     - break in system call, called by program
	breakpoint = (backtrace[1], 4, 1)

	if gca.breakpoint_insert(*breakpoint):
		gca.monitor_output("Breakpoint planted")
	else:
		breakpoint = False
		raise "Unable to set breakpoint"

	target_tid = tid
	gca.monitor_output("Target Thread %08x" % tid)

	return True

# invoked from GCA
def thread_regs_read(cpu, tid):
	if not thread_isalive(cpu, tid) or thread_getcurrent(cpu) == tid:
		regs = gca.target_regs_read(cpu)
	else:
		regs = target_os.get_thread_registers(cpu, tid)

	return regs

# invoked from GCA
def thread_regs_write(cpu, tid, regs):
	if not thread_isalive(cpu, tid):
		return False

	ret = 0
	if thread_getcurrent(cpu) == tid:
		ret = gca.target_regs_write(cpu, regs)
	else:
		ret = target_os.set_thread_registers(cpu, tid, regs)

	if ret > 0:
		return True

	return False

# invoked from GCA
def thread_mem_read(cpu, tid, addr, length):
	return gca.target_memory_read(cpu, addr, length)

# invoked from GCA
# TODO: check cpu/tid is correct
def thread_mem_write(cpu, tid, addr, data):
	ret = gca.target_memory_write(cpu, addr, data)
	if ret > 0:
		return True;
	return False

def threadlist_update(cpu):
	global thread_list

	thread_list = target_os.get_threads(cpu)

	return 1

# thread alive - gdb Txx cmd
def thread_isalive(cpu, t_id):
	threadlist_update(cpu)

	return t_id in thread_list

# current thread - gdb qC cmd
# invoked from GCA
def thread_getcurrent(cpu):
	return target_os.get_current_thread(cpu)

# extra thread info - gdb qThreadExtraInfo cmd
# invoked from GCA
def thread_getinfo(cpu, t_id):
	s = "%x" % (t_id)

	if t_id in thread_list:
		t = thread_list[t_id]
		s = "%s %04x" % (t["name"], t["current_state"] & 0xffff)

	return s

# thread list interface - gdb q[fs]ThreadInfo cmd
# invoked from GCA
def threadlist_create(cpu):
	global threads
	global first_cpu

	if first_cpu == 0:
		first_cpu = cpu

	threadlist_update(cpu)

	threads = []
	for t in thread_list:
		threads.append(t)

	return 1

# invoked from GCA
def threadlist_count(cpu):
	return len(threads)

# invoked from GCA
def threadlist_getnext(cpu):
	global threads
	out = 0
	if len(threads) > 0:
		out = threads.pop()
	return out


#symbol storage
# invoked from GCA
def symbol_getunknown():
	return symbol_storage.get_unknown()

# invoked from GCA
def symbol_add(symbol, value):
	symbol_storage.add(symbol, value)

def monitor_command(command, arg):
	if first_cpu == 0:
		return ""

	if command == "print":
		if arg == "objects":
			target_os.print_objects(first_cpu)

	return ""
