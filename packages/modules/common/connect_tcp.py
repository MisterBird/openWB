#!/usr/bin/env python3
""" Das Modul baut eine Modbus-TCP-Verbindung auf. Es gibt verschiedene Funktionen, um die gelesenen Register zu formatieren.
"""
import codecs
import paho.mqtt.publish as publish
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
import pymodbus
import struct

try:
    from ...helpermodules import log
    from ...helpermodules import pub
except:
    from pathlib import Path
    import os
    import sys
    parentdir2 = str(Path(os.path.abspath(__file__)).parents[2])
    sys.path.insert(0, parentdir2)
    from helpermodules import log
    from helpermodules import pub


class ConnectTcp:
    def __init__(self, name: str, id: int, ip_address: str, port: int) -> None:
        try:
            self.tcp_client = ModbusTcpClient(ip_address, port)
            log.MainLogger().debug("Baue Verbindung auf zu "+str(self.tcp_client))
            # Den Verbinungsaufbau übernimmt der tcp_client automatisch.
            self.name = name
            self.id = id
            self.decode_hex = codecs.getdecoder("hex_codec")
        except:
            log.MainLogger().exception(self.name)

    def close_connection(self) -> None:
        try:
            log.MainLogger().debug("Close Modbus TCP connection")
            self.tcp_client.close()
        except:
            log.MainLogger().exception(self.name)

    def __set_error_factory(self, fault_str: str, fault_state: int) -> None:
        try:
            ramdisk = Path(str(Path(os.path.abspath(__file__)).parents[3])+"/ramdisk/bootinprogress").is_file()
            if ramdisk == True:
                publish.single("openWB/set/evu/faultState", fault_state)
                publish.single("openWB/set/evu/faultStr", fault_str)
            else:
                pub.pub("openWB/set/devices/"+str(self.id)+"/get/fault_str", fault_str)
                pub.pub("openWB/set/devices/"+str(self.id)+"/get/fault_state", fault_state)
        except:
            log.MainLogger().exception(self.name)

    def __reset_error_factory(self) -> None:
        try:
            ramdisk = Path(str(Path(os.path.abspath(__file__)).parents[3])+"/ramdisk/bootinprogress").is_file()
            if ramdisk == True:
                publish.single("openWB/set/evu/faultState", 0)
                publish.single("openWB/set/evu/faultStr", "Kein Fehler.")
            else:
                pub.pub("openWB/set/devices/"+str(self.id)+"/get/fault_str", "Kein Fehler.")
                pub.pub("openWB/set/devices/"+str(self.id)+"/get/fault_state", 0)
        except:
            log.MainLogger().exception(self.name)

    def _log_connection_error(self) -> None:
        try:
            error_text = self.name+" konnte keine Verbindung aufbauen. Bitte Einstellungen (IP-Adresse, ..) und Hardware-Anschluss pruefen."
            log.MainLogger().error(error_text)
            self.__set_error_factory(error_text, 2)
        except:
            log.MainLogger().exception(self.name)

    def _log_modbus_error(self, reg: int) -> None:
        try:
            error_text = self.name+" konnte keine Werte fuer Register "+str(reg)+" abfragen. Falls vorhanden, parallele Verbindungen, zB. node red, beenden und bei anhaltender Fehlermeldung Zaehler neustarten."
            log.MainLogger().error(error_text)
            self.__set_error_factory(error_text, 1)
            self.tcp_client.close()
        except:
            log.MainLogger().exception(self.name)

    def read_integer_registers(self, reg: int, len: int, id: int) -> int:
        try:
            value = None
            resp = self.tcp_client.read_input_registers(reg, len, unit=id)
            all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
            value = int(struct.unpack('>i', self.decode_hex(all)[0])[0])
        except pymodbus.exceptions.ConnectionException:
            self._log_connection_error()
        except AttributeError:
            if type(resp) == pymodbus.exceptions.ModbusIOException:
                self._log_modbus_error(reg)
            else:
                log.MainLogger().exception(self.name)
        except:
            log.MainLogger().exception(self.name)
        else:
            self.__reset_error_factory()
        finally:
            return value

    def read_short_int_registers(self, reg: int, len: int, id: int) -> int:
        try:
            value = None
            resp = self.tcp_client.read_holding_registers(reg, len, unit=id)
            all = format(resp.registers[0], '04x')
            value = int(struct.unpack('>h', self.decode_hex(all)[0])[0])
        except pymodbus.exceptions.ConnectionException:
            self._log_connection_error()
        except AttributeError:
            if type(resp) == pymodbus.exceptions.ModbusIOException:
                self._log_modbus_error(reg)
            else:
                log.MainLogger().exception(self.name)
        except:
            log.MainLogger().exception(self.name)
        else:
            self.__reset_error_factory()
        finally:
            return value

    def read_float_registers(self, reg: int, len: int, id: int) -> float:
        try:
            value = None
            resp = self.tcp_client.read_input_registers(reg, len, unit=id)
            value = float(struct.unpack('>f', struct.pack('>HH', *resp.registers))[0])
        except pymodbus.exceptions.ConnectionException:
            self._log_connection_error()
        except AttributeError:
            if type(resp) == pymodbus.exceptions.ModbusIOException:
                self._log_modbus_error(reg)
            else:
                log.MainLogger().exception(self.name)
        except:
            log.MainLogger().exception(self.name)
        else:
            self.__reset_error_factory()
        finally:
            return value

    def read_registers(self, reg: int, len: int, id: int):
        try:
            value = None
            resp = self.tcp_client.read_input_registers(reg, len, unit=id)
            value = float(resp.registers[1])
        except pymodbus.exceptions.ConnectionException:
            self._log_connection_error()
        except AttributeError:
            if type(resp) == pymodbus.exceptions.ModbusIOException:
                self._log_modbus_error(reg)
            else:
                log.MainLogger().exception(self.name)
        except:
            log.MainLogger().exception(self.name)
        else:
            self.__reset_error_factory()
        finally:
            return value

    def read_binary_registers_to_int(self, reg: int, len: int, id: int, bit: int, signed=True) -> int:
        try:
            value = None
            resp = self.tcp_client.read_holding_registers(reg, len, unit=id)
            decoder = BinaryPayloadDecoder.fromRegisters(resp.registers, byteorder=Endian.Big, wordorder=Endian.Big)
            if bit == 32:
                if signed == True:
                    value = int(decoder.decode_32bit_int())
                else:
                    value = int(decoder.decode_32bit_uint())
            elif bit == 16:
                if signed == True:
                    value = int(decoder.decode_16bit_int())
                else:
                    value = int(decoder.decode_16bit_uint())
        except pymodbus.exceptions.ConnectionException:
            self._log_connection_error()
        except AttributeError:
            if type(resp) == pymodbus.exceptions.ModbusIOException:
                self._log_modbus_error(reg)
            else:
                log.MainLogger().exception(self.name)
        except:
            log.MainLogger().exception(self.name)
        else:
            self.__reset_error_factory()
        finally:
            return value

    def read_binary_registers_to_float(self, reg: int, len: int, id: int, bit: int) -> float:
        try:
            value = None
            resp = self.tcp_client.read_holding_registers(reg, len, unit=id)
            decoder = BinaryPayloadDecoder.fromRegisters(resp.registers, byteorder=Endian.Big, wordorder=Endian.Big)
            if bit == 32:
                value = float(decoder.decode_32bit_float())
            elif bit == 16:
                value = float(decoder.decode_16bit_float())
        except pymodbus.exceptions.ConnectionException:
            self._log_connection_error()
        except AttributeError:
            if type(resp) == pymodbus.exceptions.ModbusIOException:
                self._log_modbus_error(reg)
            else:
                log.MainLogger().exception(self.name)
        except:
            log.MainLogger().exception(self.name)
        else:
            self.__reset_error_factory()
        finally:
            return value
