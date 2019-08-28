# -*- coding: utf-8 -*-
#################################################################
#
# MCP23S17 device control
#
#
#  Copyright (C) 2019.  Takashi Totsuka. All rights reserved.
##################################################################

import FTDIAsyncBB as ftdbb


class MCP23S17(object):
    """
    This is a low level abstraction of Microchip Technology Inc's MCP23S17.

    Preconditions.

    * The hardware address lines (A0-3) of `MC23S17` is used to distinguish multiple MCP devices.
      They share the same low active chip select line.
    * Low active reset line is available to reset all the MCP devices to a known state.

    Postconditions.

    * The MCP devices are reset.
    * The `HAEN` bit of `IOCON` is set to enable hardware address mode.
    * All other registers are unchanged after reset.

    Args:
        port (FTDIAsyncBB.Port): `Port` object. The port object must have a clock, chip select, reset,
            transmit data, and receive data pins.
        pin_ck (int), pin_txd (int), pin_rxd (int): Pin numbers of the SPI clock, tx, and rx data pins.
            See FTDIAsyncBB.SPI for detail.
        pin_cs (int): Pin number of low active common chip select output.
        pin_reset (int): Pin number of low active MCP device hardware reset output.
    """
    def __init__(self, port, pin_ck, pin_txd, pin_rxd, pin_cs, pin_reset):
        # Store port object.
        self.port = port

        # Check pin existence and uniqueness of CS and RESET
        self.cs = self.port.get_pin_object(pin_cs)
        self.reset = self.port.get_pin_object(pin_reset)
        if self.cs is None or self.reset is None:
            raise ValueError("Pin does not exist in the port.")
        if len({pin_ck, pin_txd, pin_rxd, pin_cs, pin_reset}) != 5:
            raise ValueError("Pins must have unique pin numbers.")
        if not self.cs.is_output or not self.reset.is_output:
            raise ValueError("Pins do not have right in/out attribute.")
        self.spi = ftdbb.SPI(port, pin_ck, pin_txd, pin_rxd)

        # Reset the device
        self.reset_devices()

        # Set HAEN=1 to talk to each device independently.
        # Note: After reset, HAEN` is disabled and every device is mapped to device address 0.
        # Writing HAEN=1 to IOCON at device address 0 after a reset is a broadcast message
        # to move all the devices to the hardware address mode.
        self.write_register(0, 0xa, 0x88) # IOCON BANK=1, SEQ=0(ByteMode), HAEN=1

    def reset_devices(self):
        """
        Hardware reset MCP devices.
        """
        self.cs.value = 1
        self.reset.value = 0
        self.port.set_pins()
        self.reset.value = 1
        self.port.set_pins()

    def write_register(self, dev, reg, data):
        """
        Write a byte to a register of a device.

        Args:
            dev (int): Device hardware address (0-7). Only the bit 0-2 of `dev` are used.
            reg (int): Register address. Valid addresses are 0 to 0x15 (`BANK=0` 16bit mode) or
                0 to 0xA and 0x10 to 0x1A (`BANK=1` 8bit mode). See MCP23S17 data sheet for detail.
            data (int): 8 bit data to write.
        """

        # Enable /CS
        self.cs.value = 0
        self.port.set_pins()

        # Send OP code
        val = 0x40
        val |= ((dev & 0x7) << 1)
        self.spi.send_byte(val)

        # Send register address
        self.spi.send_byte(reg & 0x1f)

        # Send data
        self.spi.send_byte(data & 0xff)

        # Disable /CS
        self.cs.value = 1
        self.port.set_pins()

    def read_register(self, dev, reg):
        """
        Read a byte from a register of a device.

        Args:
            dev (int): Device hardware address (0-7). Only the bit 0-2 of `dev` are used.
            reg (int): Register address. Valid addresses are 0 to 0x15 (`BANK=0` 16bit mode) or
                0 to 0xA and 0x10 to 0x1A (`BANK=1` 8bit mode). See MCP23S17 data sheet for detail.

        Returns:
            int: A byte data read from the register.
        """
        # Enable /CS
        self.cs.value = 0
        self.port.set_pins()

        # Send OP code
        val = 0x41
        val |= ((dev & 0x7) << 1)
        self.spi.send_byte(val)

        # Send register address
        self.spi.send_byte(reg & 0x1f)

        # Receive one byte
        val = self.spi.receive_byte()

        # Disable /CS
        self.cs.value = 1
        self.port.set_pins()

        return val


if __name__ == "__main__":
    import FTDIAsyncBB as Ftdbb
    pin_ck = Ftdbb.IOPin(0, "SCK", is_output=True, init_val=0)
    pin_td = Ftdbb.IOPin(1, "STXD", is_output=True, init_val=0)
    pin_rd = Ftdbb.IOPin(2, "SRXD", is_output=False)
    pin_lcs = Ftdbb.IOPin(3, "/CS", is_output=True, init_val=1)
    pin_lres = Ftdbb.IOPin(5, "/RESET", is_output=True, init_val=1)
    port = Ftdbb.Port([pin_lres, pin_lcs, pin_ck, pin_td, pin_rd], debug_mode=False)

    # Create the MCP23S17 device control object.
    mcp = MCP23S17(port, 0, 1, 2, 3, 5)
    for a in range(11):
        v0 = mcp.read_register(0, a)
        v1 = mcp.read_register(1, a)
        print("Address {:02x}  D1 value {:02x}   D2 value {:02x}".format(a, v0, v1))
    print()
    for a in range(16, 27):
        v0 = mcp.read_register(0, a)
        v1 = mcp.read_register(1, a)
        print("Address {:02x}  D1 value {:02x}   D2 value {:02x}".format(a, v0, v1))

    a = input("Write Address:")
    a = int(a)
    v = input("Write data")
    v = int(v)
    print("Write address={}, Value={:x}".format(a, v))
    mcp.write_register(0, a, v)
    for a in range(11):
        v0 = mcp.read_register(0, a)
        v1 = mcp.read_register(1, a)
        print("Address {:02x}  D1 value {:02x}   D2 value {:02x}".format(a, v0, v1))
    print()
    for a in range(16, 27):
        v0 = mcp.read_register(0, a)
        v1 = mcp.read_register(1, a)
        print("Address {:02x}  D1 value {:02x}   D2 value {:02x}".format(a, v0, v1))