from time import sleep
from openocd_python import *

openocd = OpenOCDClient().connect()

openocd.flashWrite("nuttx.bin", 0x08000000)