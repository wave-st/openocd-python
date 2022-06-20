from time import sleep
import unittest
from openocd_python import *
from random import randrange

openocd = OpenOCDClient().connect()

if (openocd.getState() != TargetState.Halted) :
    openocd.resetHalt(blocking=True)
    print("target is halted")

address = 0x20000000

print("\n--------- Byte ---------")
randomByte = randrange(0x0, 0xFF)
print("Writing 0x%0.2x..." % randomByte)
print("previous value:")
ocdWrapper.printMemoryDict(openocd.readSingle(MemType.UINT8, address))
print("\nWrite pass: ", end="")
print(openocd.writeSingle(MemType.UINT8, address, randomByte), end="\n\n")
print("new value:")

ocdWrapper.printMemoryDict(openocd.readSingle(MemType.UINT8, address))

print("\n------- HalfWord -------")
randomHalfWord = randrange(0x0, 0xFFFF)
print("Writing 0x%0.4x..." % randomHalfWord)
print("previous value:")
ocdWrapper.printMemoryDict(openocd.readSingle(MemType.UINT16, address))
print("\nWrite pass: ", end="")
print(openocd.writeSingle(MemType.UINT16, address, randomHalfWord), end="\n\n")
print("new value:")

ocdWrapper.printMemoryDict(openocd.readSingle(MemType.UINT16, address))

print("\n--------- Word ---------")
randomWord = randrange(0x0, 0xFFFFFFFF)
print("Writing 0x%0.8x..." % randomWord)
print("previous value:")
ocdWrapper.printMemoryDict(openocd.readSingle(MemType.UINT32, address))
print("\nWrite pass: ", end="")
print(openocd.writeSingle(MemType.UINT32, address, randomWord), end="\n\n")
print("new value:")

ocdWrapper.printMemoryDict(openocd.readSingle(MemType.UINT32, address))

print("\n-------- Double --------")
randomDouble = randrange(0x0, 0xFFFFFFFFFFFFFFFF)
print("Writing 0x%0.8x..." % randomDouble)
print("previous value:")
ocdWrapper.printMemoryDict(openocd.readSingle(MemType.UINT64, address))
print("\nWrite pass: ", end="")
print(openocd.writeSingle(MemType.UINT64, address, randomDouble), end="\n\n")
print("new value:")

ocdWrapper.printMemoryDict(openocd.readSingle(MemType.UINT64, address))