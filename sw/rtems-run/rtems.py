
import gca
from gca_util import *

class rtems:
	_OBJECTS_APIS = ["NO_API", "INTERNAL_API", "CLASSIC_API", "POSIX_API", "ITRON_API"]

	_OBJECTS = [
		[""],
		["", "THREADS", "MUTEXES"],
		["", "TASKS", "TIMERS", "SEMAPHORES", "QUEUES", "PARTITIONS", "REGIONS", "PORTS", "PERIODS", "EXTENSIONS", "BARRIERS"],
	]


	_OI_TAB = "_Objects_Information_table"

	_UNK_SYMBOLS = {
		"_Objects_Information_table",
		"_Thread_Executing",
		"_Thread_Idle",
		"_Thread_Heir",
		"_CPU_Context_switch",
		"_Thread_Dispatch",
	}

	thread_list = {}

	def __init__(self, ss, t_cpu):
		self._symbol_storage = ss
		self._target_cpu = t_cpu

		ss.add_unknown(self._UNK_SYMBOLS)

	def get_objectinfo_table(self, cpu):
		if not self._symbol_storage.exists(self._OI_TAB):
			return []
		
		addr = self._symbol_storage.get(self._OI_TAB)
		info_ptrs = read_table(cpu, addr, len(self._OBJECTS_APIS))

		return info_ptrs

	def get_objectinfo(self, cpu, addr):
		data = gca.target_memory_read(cpu, addr, 64)

		api = unpack("I", data[:4])[0]
		clas = unpack("H", data[4:6])[0]
		maximum = unpack("H", data[16:18])[0]
#		allocation_size = unpack("H", data[22:24])[0]
#		size = unpack("I", data[24:28])[0]
		local_table = unpack("I", data[28:32])[0]

		out = {"api": api, "class": clas, "maximum": maximum, "local_table": local_table}

		return out

	def get_objectcontrol(self, cpu, addr):
		data = gca.target_memory_read(cpu, addr, 4*4)
		oc = unpack("IIII", data)

		out = {
			"next": oc[0],
			"prev": oc[1],
			"id": oc[2],
			"name": data[15:11:-1],
		}

		return out

	def print_objects(self, cpu):
		ptrs = self.get_objectinfo_table(cpu)

		for i in range(1, len(ptrs)):
			if ptrs[i] == 0:
				continue


			for j in range(1, len(self._OBJECTS[i])):

				oi_ptr = deref_ptr(cpu, ptrs[i] + 4 * j)
				oi = self.get_objectinfo(cpu, oi_ptr)

				for k in range(0, oi["maximum"] + 1):
					objctrl_ptr = deref_ptr(cpu, oi["local_table"] + k * 4)
					if objctrl_ptr == 0:
						continue

					oc = self.get_objectcontrol(cpu, objctrl_ptr)
					gca.monitor_output("%s %s %08x %s" % (self._OBJECTS_APIS[i], self._OBJECTS[i][j], oc["id"], repr(oc["name"])))


	def get_threadcontrol(self, cpu, addr):
		if addr == 0:
			return False

		data = gca.target_memory_read(cpu, addr, 5*4+4)
		tc = unpack("IIIIII", data)

		reg = gca.target_memory_read(cpu, addr + 0xd0, 6*4)

		reg_fp_data = gca.target_memory_read(cpu, addr + 0xe8, 4)
		reg_fp_ptr = unpack_int(reg_fp_data)

		out = {
			"id": tc[2],
			"name": data[15:11:-1],
			"current_state": tc[4],
			"registers": {
				"eflags": reg[0:4],
				"esp": reg[4:8],
				"ebp": reg[8:12],
				"ebx": reg[12:16],
				"esi": reg[16:20],
				"edi": reg[20:24]
			},
			"registers_fp": reg_fp_ptr
		}

		return out

	def get_current_thread(self, cpu):
		if not self._symbol_storage.exists("_Thread_Executing"):
			return 1

		thread_ctrl_ptr = deref_ptr(cpu, self._symbol_storage.get("_Thread_Executing"))
		thread_control = self.get_threadcontrol(cpu, thread_ctrl_ptr)

		return thread_control["id"]

	def get_threads(self, cpu):
		thread_list = {}

		ptrs = self.get_objectinfo_table(cpu)
		for i in range(1, len(ptrs)):
			#print "Parsing API: %s" % self._OBJECTS_APIS[i]
			if ptrs[i] == 0:
				continue

			oi_ptr = deref_ptr(cpu, ptrs[i] + 4) # +4 to get TASKS (offset 1)
			oi = self.get_objectinfo(cpu, oi_ptr)

			for i in range(0, oi["maximum"] + 1):
				thread_ctrl_ptr = deref_ptr(cpu, oi["local_table"] + i * 4)
				if thread_ctrl_ptr == 0:
					continue

				thread_control = self.get_threadcontrol(cpu, thread_ctrl_ptr)
				#print "%04x " % thread_control["id"]

				if thread_control["current_state"] & 1 == 0: # filter dormant threads
					tid = thread_control["id"]
					thread_list[tid] = thread_control

		# cache the result
		self.thread_list = thread_list

		return thread_list

	def get_thread_registers(self, cpu, tid):
		thread = self.thread_list[tid]
		t_regs = thread["registers"]

		#FIXME: this is probably wrong eip
		t_regs["eip"] = gca.target_memory_read(cpu, unpack_int(t_regs["esp"]), 4)

		# fp working regs
		# TODO: add missing fp regs, are they even preserved??!
		if thread["registers_fp"] != 0:
			for i in range(0, 8):
				t_regs["fp%d" % i] = gca.target_memory_read(cpu, thread["registers_fp"] + i * 10, 10)

		return self._target_cpu.get_gdb_regs(t_regs)

	def set_thread_registers(self, cpu, tid, regs):
		r = self._target_cpu.parse_gdb_regs(regs)
		gca.monitor_output("Not implemented, yet")
		return 0

