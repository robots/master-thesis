source ../source-qemu

export PYTHONPATH=./

qemu-system-i386 -gdb tcp:localhost:10000 -m 128 -boot a -fda boot.img -hda fat:./hda --no-reboot
#qemu-system-i386 -gca gca_rtems -gdb tcp:localhost:10000 -m 128 -boot a -fda boot.img -hda fat:./hda --no-reboot

#qemu-i386 -gdb tcp:localhost:10000 -m 128 -boot a -fda boot.img -hda fat:./hda --no-reboot
