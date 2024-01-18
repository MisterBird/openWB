#!/usr/bin/python3
import sys
from pymodbus.client.sync import ModbusSerialClient

register = 1000 #int(sys.argv[1])
value = int(sys.argv[1]) * 100

client = ModbusSerialClient(method = "rtu", port="/dev/ttyUSB0", baudrate=9600, stopbits=1, bytesize=8, timeout=1)
rq = client.write_registers(register, value, unit=1)
