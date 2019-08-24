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

        self.mcp.write_register(1, 0, 0xff)  # IODIRA all bits are input
        self.mcp.write_register(1, 0x10, 0xff)  # IODIRB all bits are input
        self.mcp.write_register(1, 0x6, 0xff)  # GPPUA pull up all bits
        self.mcp.write_register(1, 0x16, 0xff)  # GPPUB pull up all bits

        # Create the GUI panel
        self.main_panel = GUI.MainPanel()
        self.main_panel.set_clear_callback(self._clear_cb)
        self.main_panel.set_run_callback(self._run_cb)

    def _clear_cb(self):
        print("Clear call back is called")

    def _run_cb(self, a, b, is_plus=True):
        print("Run call back is called A={}, B={}, OP={}".format(a, b, "ADD" if is_plus else "SUB"))
        # This is a temporary hack
        y = (a + b) if is_plus else (a - b)
        self.main_panel.set_output_value(y)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mc = MainControl()
    sys.exit(app.exec_())
