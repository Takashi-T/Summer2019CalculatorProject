# -*- coding: utf-8 -*-
#################################################################
#
# Asynchronous Big Bang I/O for FTDI chips.
#
#
#
#
#  Copyright (C) 2019.  Takashi Totsuka. All rights reserved.
##################################################################

import time

# Uses ftd2xx. This is a Python wrapper for FTDI's D2XX library.
import ftd2xx


class IOPin(object):
    """
    This is an abstraction of each GPIO pins in the asynchronous big bang mode.
    Values set to the pins can be sent via USB to the FTDI device and those values will appear
    on the physical output pins. Similarly, values on the physical input pins will be copied to
    the Pin objects.

    Args:
        num (int): Physical pin number in the range of 0 to 7.
        name (str): Name of the pin.
        is_output (bool): True if this is an output pin.
        init_val (int): Initial value of the pin. If the pin is an output pin, the value will appear immediately
            after the Port object is created and initialized.
    """
    def __init__(self, num, name, is_output=False, init_val=0):
        self.no = num
        self.name = name
        self.is_output = is_output
        self.value = 1 if init_val else 0


class Port(object):
    """
    Create and initialize the FTDI Big Bang I/O port.

    Args:
        pin_list: List of IOPin objects for each pins used in GPIO operation. Pins available on
            the FTDI device but not specified here are set as input pins.
            Each pin object must have unique physical pin number.
        debug_mode (bool): True: Communicate to the real FTDI device. False: Do not access FTDI device.
    """

    # FTDI operation mode
    FTD_RESET = 0
    FTD_ASYNCH_BITBANG_MODE = 0x1
    # Maximum number of bytes sent in one USB packet
    TXD_PACKET_MAX = 16
    # FTDI device open retry count
    MAX_OPEN_RETRY = 5
    # Debug mode signal chart length
    SIGNAL_LOG_SIZE = 100

    def __init__(self, pin_list, debug_mode=False):
        self.pin_list = pin_list
        self.debug_mode = debug_mode
        self.ftd = None
        self.txd_buf = []
        self.signal_history = []
        self._debug_read_data = 0

        # Process pin definition list
        if self.pin_list is None or len(self.pin_list) == 0:
            raise ValueError("Valid pin definition list not supplied")
        pin_dict = {}
        active_pin_mask = 0
        output_pin_mask = 0
        for pin in self.pin_list:
            # Check input parameters
            if not isinstance(pin, IOPin):
                raise ValueError("An IOPin object must be supplied as a pin")
            pin.no = int(pin.no)
            if not (0 <= pin.no < 8):
                raise ValueError("Pin number {} is out of range".format(pin.no))
            pin_mask = 1 << pin.no
            if pin_mask & active_pin_mask:
                raise ValueError("Pin number {} is not unique".format(pin.no))
            if pin.name in pin_dict:
                print("Warning: Pin name '{}' is not unique".format(pin.name))

            # Register the pin to the dictionary
            pin_dict[pin.no] = pin
            active_pin_mask |= pin_mask
            if pin.is_output:
                output_pin_mask |= pin_mask
            # Normalize the initial value
            pin.value = 0 if pin.value == 0 else 1

        self.pin_table = pin_dict
        self.output_pins = output_pin_mask
        self.input_pins = active_pin_mask & ~output_pin_mask

        # Open and initialize the FTDI device.
        # The initialization sequence is based on FTDI's application note
        # https://www.ftdichip.com/Support/Documents/AppNotes/AN_135_MPSSE_Basics.pdf
        if not debug_mode:
            # Open the device.
            retry_count = 0
            while self.ftd is None:
                try:
                    self.ftd = ftd2xx.open(0)
                except ftd2xx.DeviceError:
                    if retry_count >= Port.MAX_OPEN_RETRY:
                        raise OSError("Can't open an FTDI device")
                    retry_count += 1
                    print("Retrying opening an FTDI device.")
                    time.sleep(1)
                else:
                    break

            # Reset the FTDI device
            self.ftd.resetDevice()

            # Set high baud rate.
            # A high baud rate is chosen to prevent FTDI chip's write FIFO overflow as well as
            # reading a data before all the previously sent data have appeared on output pins.
            # FTDI recommends a baud rate less than 1MHz in their application notes.
            # Note that the actual clock is baud rate x 16.
            self.ftd.setBaudRate(57600)  # Clock freq. is about 920 kHz (1.1uS).

            # Set Asynchronous bit bang mode
            self.ftd.setBitMode(0, Port.FTD_RESET)   # Reset I/O ports
            self.ftd.setBitMode(self.output_pins, Port.FTD_ASYNCH_BITBANG_MODE)

            # Wait for 50mS for the FTDI chip to work in the new mode.
            time.sleep(0.05)

        # Set the initial values to the ports
        self.set_pins()

    def __del__(self):
        if self.ftd is not None:
            self.ftd.close()
            self.ftd = None

    def __str__(self):
        return "{} pins, Output={:08b}, Input={:08b}".format(len(self.pin_list),
                                                             self.output_pins, self.input_pins)

    def get_pin_object(self, pin_no):
        """
        Returns the IOPin object that has the specified pin number.

        Args:
            pin_no (int): Pin number.

        Returns:
            IOPin : The Pin object. If a pin is not defined for the pin number, `None` is returned.
        """
        return self.pin_table[pin_no] if pin_no in self.pin_table else None

    def _assemble_write_data(self):
        val = 0
        for pin in self.pin_list:
            if not pin.is_output or pin.value == 0:
                continue
            val |= (1 << pin.no)

        return val

    def _flush_txbuf(self):
        if len(self.txd_buf) == 0:
            return

        # Copy data in the signal history buffer
        self.signal_history += self.txd_buf
        n_over = len(self.signal_history) - Port.SIGNAL_LOG_SIZE
        if n_over > 0:
            del self.signal_history[0:n_over]

        # Send to the FTDI device
        if not self.debug_mode:
            xbuf = bytes(self.txd_buf)
            n_written = self.ftd.write(xbuf)
            if n_written != len(self.txd_buf):
                print("ERROR: FTDIAsyncBB._flush_txbuf: Write {} bytes, actual {} bytes".format(
                    len(self.txd_buf), n_written))

        # Clear the transmission buffer anyway
        self.txd_buf.clear()

    def set_pins(self, flush=True):
        """
        Send output pin values to the FTDI chip on a target hardware. By default, the values are sent
        immediately to the hardware and appear on physical output pins.
        If you prefer to pack multiple output data and send them in single USB packet, set `flush` to `False`.
        The packed data will appear at the output pins one by one at the rate of FTDI's baud rate clock
        (x16 of FTDI's baud rate setting).
        If the amount of unsent data in the transmission buffer is greater or equal to `TXD_PACKET_MAX` bytes,
        they are sent automatically.

        Args:
            flush (bool): `True`: Send the pin values immediately via USB to an FTDI device.
                `False`: Store the pin values in a buffer for future transmission.

        Returns: None.

        Examples::

            pin_txd = IOPin(1, "TXD", is_output=True, init_val=0)
            pin_clk = IOPin(3, "CLK", is_output=True, init_val=0)
            gpio = Port([pin_txd, pin_clk])

            # Set data and toggle the clock with single USB packet to the target hardware
            pin_txd.value = data
            gpio.set_pins(flush=False)
            pin_clk.value = 1
            gpio.set_pins(flush=False)
            pin_clk.value = 0
            gpio.set_pins(flush=True)
        """
        xmit_data = self._assemble_write_data()

        # Send the data
        self.txd_buf.append(xmit_data)
        if flush or (len(self.txd_buf) >= Port.TXD_PACKET_MAX):
            self._flush_txbuf()

    def get_pins(self):
        """
        Get physical input pin values and store these values to the corresponding `IOPin` objects.
        If there is any pending output data in the transmission buffer, they are sent to an FTDI device
        and appear on physical output pins before the physical input pin data are read.
        """
        if self.debug_mode:
            raw_val = self._debug_read_data  # Copy fake read data for debug purpose
        else:
            # Make sure all the xmit data is sent out before reading.
            self._flush_txbuf()
            # Read the GPIO pins.
            raw_val = self.ftd.getBitMode()

        for pin in self.pin_list:
            if pin.is_output:
                continue
            pin.value = (raw_val >> pin.no) & 1

        return

    def _print_signal_log(self):
        for pin in self.pin_list:
            print("{:>6} ".format(pin.name), end="")
            for d in self.signal_history:
                v = (d >> pin.no) & 1
                print("{}".format("H" if v else "L"), end="")
            print()

        print()
        self.signal_history.clear()


class SPI(object):
    """
    This is a utility class that implements SPI protocol on top of the `Port` API.
    SPI mode (0,0) is used.
    In SPI (0,0), clock is idle at low level (CPOL=0). Also in SPI (0,0), data is output at
    the falling edge and is sampled at the rising edge (CPHA=0).

    Preconditions.

    * The Port object is created and dedicated clock, transmit data (MOSI), receive data (MISO)
      pins are assigned.
    * Chip select and reset (if any) are properly controlled before and after calling
      transmit/receive methods.

    Args:
        port (Port): A `Port` object used for SPI interface. The object must include a clock, transmit data,
            and receive data pins.
        pin_ck (int): Pin number of a clock output (SPI CPOL=0).
        pin_txd (int): Pin number of a transmit data output or MOSI.
        pin_rxd (int): Pin number of a receive data input or MISO.
    """
    def __init__(self, port, pin_ck, pin_txd, pin_rxd):
        # Store port object.
        self.port = port

        # Check pin existence and uniqueness
        self.ck = self.port.get_pin_object(pin_ck)
        self.txd = self.port.get_pin_object(pin_txd)
        self.rxd = self.port.get_pin_object(pin_rxd)
        if self.ck is None or self.txd is None or self.rxd is None:
            raise ValueError("Pin does not exist in the port.")
        if len({pin_ck, pin_txd, pin_rxd}) != 3:
            raise ValueError("Pins must have unique pin numbers.")
        if not self.ck.is_output or not self.txd.is_output or self.rxd.is_output:
            raise ValueError("Pins do not have right in/out attribute.")

        # Make sure CLK is low (idle)
        self.ck.value = 0
        self.port.set_pins()

    def send_byte(self, value):
        """
        Send one byte data via SPI.

        Args:
            value (int): A byte data to be sent.
        """

        # Check the clock. SPI mode 0,0 requires CLK=0 during idle.
        if self.ck.value != 0:
            print("Warning: FTDIAsyncBB.SPI.send_byte: clock is not low.")
            self.ck.value = 0
            self.port.set_pins()

        # Serialize and send one byte. MSB first.
        for i in range(7, -1, -1):
            # Feed one bit data to the MPC23S17
            self.ck.value = 0
            self.txd.value = (value >> i) & 1
            self.port.set_pins(flush=False)

            # Then send a clock pulse
            self.ck.value = 1
            self.port.set_pins(flush=False)

        self.ck.value = 0
        self.port.set_pins()

    def receive_byte(self):
        """
        Receive one byte data via SPI.

        Returns:
            int: Received byte data.
        """
        # Check the clock. SPI mode 0,0 requires CLK=0 during idle.
        if self.ck.value != 0:
            print("Warning: FTDIAsyncBB.SPI.receive_byte: clock is not low.")
            self.ck.value = 0
            self.port.set_pins()

        # Read 8 bits and deserialize
        # Note: Since the clock is brought to L already, the data is present.
        val = 0
        # Read the remaining 7 bits.
        for i in range(7, -1, -1):
            # Read the SOUT of the MPC23S17
            val <<= 1

            # Read the new bit
            self.port.get_pins()
            val |= self.rxd.value

            # Then send a clock pulse
            self.ck.value = 1
            self.port.set_pins(flush=False)
            self.ck.value = 0
            self.port.set_pins()

        return val

if __name__ == "__main__":
    pin_ck = IOPin(0, "SCK", is_output=True, init_val=0)
    pin_td = IOPin(1, "STXD", is_output=True, init_val=0)
    pin_rd = IOPin(2, "SRXD", is_output=False)
    pin_lcs = IOPin(3, "/CS", is_output=True, init_val=1)
    port = Port([pin_lcs, pin_ck, pin_td, pin_rd], debug_mode=False)
    for _ in range(5):
        v = input("Value ")
        v = int(v)
        pin_ck.value = v & 1
        pin_td.value = (v >> 1) & 1
        pin_lcs.value = (v >> 3) & 1
        port.set_pins()