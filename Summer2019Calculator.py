# -*- coding: utf-8 -*-
#################################################################
#
# The Calculator Project for Summer 2019.
#
#   Main program.
#
#
#  Copyright (C) 2019.  Takashi Totsuka. All rights reserved.
##################################################################

import GUI
import FTDIAsyncBB as Ftdbb
import MCP23S17 as mcp

from PyQt5.QtWidgets import QApplication
import sys
import time


class MainControl(object):
    def __init__(self):
        # Create the FTDI port object.
        self.pin_ck = Ftdbb.IOPin(0, "SCK", is_output=True, init_val=0)
        self.pin_td = Ftdbb.IOPin(1, "STXD", is_output=True, init_val=0)
        self.pin_rd = Ftdbb.IOPin(2, "SRXD", is_output=False)
        self.pin_lcs = Ftdbb.IOPin(3, "/CS", is_output=True, init_val=1)
        self.pin_lres = Ftdbb.IOPin(5, "/RESET", is_output=True, init_val=1)
        self.port = Ftdbb.Port([self.pin_lres, self.pin_lcs, self.pin_ck, self.pin_td, self.pin_rd],
                               debug_mode=False)

        # Create the MCP23S17 device control object.
        self.mcp = mcp.MCP23S17(self.port, 0, 1, 2, 3, 5)

        # Device 0
        self.mcp.write_register(0, 0, 0x0)  # IODIRA all bits are output
        self.mcp.write_register(0, 0x10, 0x0)  # IODIRB all bits are output
        self.mcp.write_register(0, 0x6, 0xff)  # GPPUA pull up all bits
        self.mcp.write_register(0, 0x16, 0xff)  # GPPUB pul up all bits

        # Device 1
        self.mcp.write_register(1, 0, 0xff)  # IODIRA all bits are input
        self.mcp.write_register(1, 0x10, 0xff)  # IODIRB all bits are input
        self.mcp.write_register(1, 0x6, 0xff)  # GPPUA pull up all bits
        self.mcp.write_register(1, 0x16, 0xff)  # GPPUB pull up all bits
        self.mcp.write_register(1, 0x1, 0xff)  # IPOLA all bits are active low
        self.mcp.write_register(1, 0x11, 0xff)  # IPOLB all bits are active low

        # Create the GUI panel
        self.main_panel = GUI.MainPanel()
        self.main_panel.set_clear_callback(self._clear_cb)
        self.main_panel.set_run_callback(self._run_cb)

    def _clear_cb(self):
        print("Clear call back is called")

        # Clear ports A and B
        self.mcp.write_register(0, 0x9, 0)  # Set 0 to GPIOA (A port)
        self.mcp.write_register(0, 0x19, 0)  # Set 0 to GPIOB (B port)

    def _run_cb(self, a, b, is_plus=True):
        print("Run call back is called A={}, B={}, OP={}".format(a, b, "ADD" if is_plus else "SUB"))

        # Set values to the A and B ports
        self.mcp.write_register(0, 0x9, a & 0xff)  # Set A value to GPIOA
        self.mcp.write_register(0, 0x19, b & 0xff)  # Set B value to GPIOB

        # # Sense and collect output port till the value converges.
        # l_outvalues = []
        # l_timestamp = []
        # start_time = time.time()
        # for _ in range(20):
        #     t1 = time.time()
        #     vl = self.mcp.read_register(1, 0x9)  # Read b0-7 from GPIOA
        #     vh = self.mcp.read_register(1, 0x19)  # Read b8 from GPIOB
        #     t2 = time.time()
        #     v = ((vh & 1) << 8) | (vl & 0xff)
        #     l_outvalues.append(v)
        #     l_timestamp.append((t1 + t2)/2.0 - start_time)
        #
        #     # Check if the value converges.
        #     if len(l_outvalues) < 3:
        #         continue
        #     if l_outvalues[-1] == l_outvalues[-2] == l_outvalues[-3]:
        #         break

        # self.main_panel.set_output_value(l_outvalues[-1])

        # This is a temporary hack
        # y = (a + b) if is_plus else (a - b)
        vl = self.mcp.read_register(1, 0x9)  # Read b0-7 from GPIOA
        vh = self.mcp.read_register(1, 0x19)  # Read b8 from GPIOB
        print("VL={:x}, VH={:x}".format(vl, vh))
        y = ((vh & 1) << 8) | (vl & 0xff)
        self.main_panel.set_output_value(y)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mc = MainControl()
    sys.exit(app.exec_())
