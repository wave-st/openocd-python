#!/usr/bin/env python3

from enum import Enum
#from posixpath import split
import socket
import itertools
import time
import re
from loguru import logger


class MemType(Enum):
    UINT64 = 64
    UINT32 = 32
    UINT16 = 16
    UINT8 = 8
    UINT7 = 7
    UINT6 = 6
    UINT5 = 5
    UINT4 = 4
    UINT3 = 3
    UINT2 = 2
    BIT = 1


class TargetState(Enum):
    Running = "running" # opendocd target state
    Halted = "halted" # opendocd target state
    DebugRunning = "debug-running" # opendocd target state
    Reset = "reset" # opendocd target state
    Unknown = "unknown" # opendocd target state
    Error = "error" # error signal state

class Register():
    def __init__(self, name, len):
        self.name = name
        self.len = len


def printMemoryDict(mem_dict):
    print("addr        val")
    for address, value in mem_dict.items() :
        print(("0x%0.8x" % address) + "  " + ("0x%0.8x" % value))


class OpenOCDClient():
    COMMAND_TOKEN = '\x1a'

    def __init__(self, verbose=False, tcl_ip="127.0.0.1", tcl_port=6666):
        self.verbose = verbose
        self.tcl_ip = tcl_ip
        self.tcl_port = tcl_port
        self.buffer_size = 4096
        self.tcl_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.state = TargetState.Unknown
        self.targetName = "unknown"
        self.endianness = "unknown"
        self.chipName = "unknown"
        self.cpuTAPid = "unknown"
        self.workAreaSize = "unknown"

    def connect(self):
        self.tcl_socket.connect((self.tcl_ip, self.tcl_port))
        self.targetName = self.getTargetName()
        self.endianness = self.getEndianness()
        self.chipName = self.getChipName()
        self.cpuTAPid = self.getCPUTAPID()
        self.workAreaSize = self.getWorkAreaSize()

        self.getState()
        logger.info("connected to openocd on " + self.tcl_ip + " port " + str(self.tcl_port))
        logger.info("Target name: " + self.targetName)
        logger.info("Endianness: " + self.endianness)
        logger.info("Chip name: " + self.chipName)
        logger.info("CPU TAP ID: " + self.cpuTAPid)
        logger.info("Work Area Size: " + self.workAreaSize)

        return self


    def disconnect(self, type, value, traceback):
        try:
            self.send("exit")
        finally:
            self.tcl_socket.close()


    def captureCommand(self, cmd):
        return self.send('capture "' + cmd + '"').rstrip()

    def getTargetName(self):
        return self.captureCommand("echo $_TARGETNAME")

    def getEndianness(self):
        return self.captureCommand("echo $_ENDIAN")

    def getChipName(self):
        return self.captureCommand("echo $_CHIPNAME")
    
    def getCPUTAPID(self):
        return self.captureCommand("echo $_CPUTAPID")

    def getWorkAreaSize(self):
        return self.captureCommand("echo $_WORKAREASIZE")


    def send(self, cmd):
        """Send a command string to TCL RPC. Return the result that was read."""
        if self.verbose:
            print(cmd)
        data = (cmd + OpenOCDClient.COMMAND_TOKEN).encode("utf-8")
        if self.verbose:
            print("<- ", data)

        self.tcl_socket.send(data)
        return self.receive()


    def receive(self):
        """Read from the stream until the token (\x1a) was received."""
        data = bytes()
        while True:
            chunk = self.tcl_socket.recv(self.buffer_size)
            data += chunk
            if bytes(OpenOCDClient.COMMAND_TOKEN, encoding="utf-8") in chunk:
                break

        if self.verbose:
            print("-> ", data)

        data = data.decode("utf-8").strip()
        data = data[:-1]  # strip trailing \x1a

        return data


    def readSingle(self, size, address, physical=False) :
        phys = ""
        if physical :
            phys = "phys"

        if (size == MemType.UINT64) :
            return self.decodeMemoryString(self.send("mdd %s 0x%0.8x" % (phys, address)))
        elif (size == MemType.UINT32) :
            return self.decodeMemoryString(self.send("mdw %s 0x%0.8x" % (phys, address)))
        elif (size == MemType.UINT16) :
            return self.decodeMemoryString(self.send("mdh %s 0x%0.8x" % (phys, address)))
        elif (size == MemType.UINT8) :
            return self.decodeMemoryString(self.send("mdb %s 0x%0.8x" % (phys, address)))
        else :
            return None


    def writeSingle(self, size, address, value, check=True, physical=False) :
        phys = ""
        if physical :
            phys = "phys"

        if (size == MemType.UINT64) :
            self.send("mwd %s 0x%0.8x 0x%0.8x" % (phys, address, value))
       
        elif (size == MemType.UINT32) :
            self.send("mww %s 0x%0.8x 0x%0.4x" % (phys, address, value))

        elif (size == MemType.UINT16) :
            self.send("mwh %s 0x%0.8x 0x%0.2x" % (phys, address, value))

        elif (size == MemType.UINT8) :
            self.send("mwb %s 0x%0.8x 0x%0.1x" % (phys, address, value))
        else :
            return None

        if (check) :
            readMem = self.readSingle(size, address, physical)
            if(readMem[address] != value):
                logger.error("write fail, are you sure this memory is writable ?")
                return False

        return True


    def writeDouble(self, address, check=True, physical=False):
        return self.writeSingle(MemType.UINT64, address, check, physical)

    def writeWord(self, address, check=True, physical=False):
        return self.writeSingle(MemType.UINT32, address, check, physical)

    def writeHalfWord(self, address, check=True, physical=False):
        return self.writeSingle(MemType.UINT16, address, check, physical)

    def writeByte(self, address, check=True, physical=False):
        return self.writeSingle(MemType.UINT8, address, check, physical)

    def readDouble(self, address, physical=False):
        return self.readSingle(MemType.UINT64, address, physical)

    def readWord(self, address, physical=False):
        return self.readSingle(MemType.UINT32, address, physical)

    def readHalfWord(self, address, physical=False):
        return self.readSingle(MemType.UINT16, address, physical)

    def readByte(self, address, physical=False):
        return self.readSingle(MemType.UINT8, address, physical)


    def writeMemory(self, size, memory_dict, physical=False):
        phys = ""
        if physical :
            phys = "phys"

        for address, value in memory_dict.items() :
            if (size == MemType.UINT64) :
                self.send("mwd %s 0x%0.8x 0x%0.8x" % (phys, address, value))
            elif (size == MemType.UINT32) :
                self.send("mww %s 0x%0.8x 0x%0.4x" % (phys, address, value))
            elif (size == MemType.UINT16) :
                self.send("mwh %s 0x%0.8x 0x%0.2x" % (phys, address, value))
            elif (size == MemType.UINT8) :
                self.send("mwb %s 0x%0.8x 0x%0.1x" % (phys, address, value))
            else :
                return None
        return True


    def readMemory(self, wordtype, address, n, physical=False): # todo: handle physical address
        phys = ""
        if physical :
            phys = "phys"

        output_dict = dict()

        for mem_addr in range(address, address + n + 1) :
            if (wordtype == MemType.UINT64) :
                output_dict.update(self.decodeMemoryString(self.send("mdd %s 0x%0.8x" % (phys, mem_addr))))
            elif (wordtype == MemType.UINT32) :
                output_dict.update(self.decodeMemoryString(self.send("mdw %s 0x%0.8x" % (phys, mem_addr))))
            elif (wordtype == MemType.UINT16) :
                output_dict.update(self.decodeMemoryString(self.send("mdh %s 0x%0.8x" % (phys, mem_addr))))
            elif (wordtype == MemType.UINT8) :
                output_dict.update(self.decodeMemoryString(self.send("mdb %s 0x%0.8x" % (phys, mem_addr))))
            else :
                raise Exception("incorrect word length")

        return output_dict


    def readRegister(self, reg):
        raw = self.send("reg {} force".format(reg))
        value = raw.split(":")[1].strip()

        return int(value, 16)


    def writeRegister(self, reg, value):
        self.send("reg {} {:#x}".format(reg, value))


    def getAvailableRegisters(self):
        regs = dict()
        str_res = self.captureCommand("reg")
        regs_str = re.findall(r"\((\d+)\) (\S+) \(/(\d+)\)", str_res)
        for r in regs_str :
            regs.update({r[1] : MemType(int(r[2]))})
        return regs


    def reset_cmd(self, str_cmd):
        self.send("reset %s" % (str_cmd))


    def halt(self, blocking=False, retries=5, sleepBetweenRetries=1):
        self.send("halt")
        if(blocking):
            self.waitForState(TargetState.Halted, retries, sleepBetweenRetries)


    def waitForState(self, targetState, retries=-1, sleepBetweenRetries=1):
        blocking = False
        if retries < 0 : 
            blocking = True

        while self.getState() != targetState and (blocking or retries > 0) :
                time.sleep(sleepBetweenRetries)
                retries -= 1
    

    def reset(self, blocking=False, retries=5, sleepBetweenRetries=1) :
        if(blocking):
            self.waitForState(TargetState.Reset, retries, sleepBetweenRetries)


    def resetHalt(self, blocking=False, retries=5, sleepBetweenRetries=1):
        self.reset_cmd("halt")
        if(blocking):
            self.waitForState(TargetState.Halted, retries, sleepBetweenRetries)


    def getState(self):
        try :
            self.state = TargetState(self.send("$_TARGETNAME curstate"))
        except :
            logger.error("target state error")
            self.state = TargetState.Error
        return self.state


    def resume(self, blocking=False, retries=5, sleepBetweenRetries=1):
        self.send("resume")
        if(blocking):
            self.waitForState(TargetState.Running, retries, sleepBetweenRetries)


    def halt(self, blocking=False, retries=5, sleepBetweenRetries=1):
        self.send("halt")
        if(blocking):
            self.waitForState(TargetState.Halted, retries, sleepBetweenRetries)


    def command(self, cmd, capture=True, verbose=False): # send any command to openocd
        if verbose :
            logger.warning("sending custom command: " + cmd)
        return self.captureCommand(cmd) if capture else self.send(cmd)


    def decodeMemoryString(self, str):
        splitted = str.rstrip().split(":")
        if (len(splitted) != 2) :
            return None
        return { int(splitted[0], 16) : int(splitted[1], 16) }
