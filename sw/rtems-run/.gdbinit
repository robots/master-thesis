target remote 127.0.0.1:10000

monitor gca_script load gca_rtems

add-symbol-file hda/triple_period.exe 0x00100000

info threads

monitor gca print objects
