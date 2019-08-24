#################################################################
#
# Test FTDI Async BB module.
#
#################################################################

import unittest

import FTDIAsyncBB as ftdbb

class Test_initialization_wrong_args(unittest.TestCase):
    def setUp(self):
        self.pin_ck = ftdbb.IOPin(0, "SCK", is_output=True, init_val=0)
        self.pin_td = ftdbb.IOPin(1, "STXD", is_output=True, init_val=0)
        self.pin_rd = ftdbb.IOPin(2, "SRXD", is_output=False)
        self.pin_lcs = ftdbb.IOPin(3, "/CS", is_output=True, init_val=1)
        self.pin_lres = ftdbb.IOPin(5, "/RESET", is_output=True, init_val=1)

    def test_wrong_args(self):
        with self.assertRaisesRegex(ValueError, "Valid pin.*"):
            ftdbb.Port([], debug_mode=True)

        with self.assertRaisesRegex(ValueError, "IOPin"):
            ftdbb.Port([1, 2, 3], debug_mode=True)

        # with self.assertRaisesRegex(ValueError, "SCK.*not unique"):
        #     ftdbb.Port([self.pin_ck, ftdbb.IOPin("SCK", 7)], debug_mode=True)

        with self.assertRaisesRegex(ValueError, "out of range"):
            ftdbb.Port([self.pin_ck, ftdbb.IOPin(-1, "TEST")], debug_mode=True)

        with self.assertRaisesRegex(ValueError, "out of range"):
            ftdbb.Port([self.pin_ck, ftdbb.IOPin(8, "TEST")], debug_mode=True)

        with self.assertRaisesRegex(ValueError, "Pin number.*not unique"):
            ftdbb.Port([self.pin_ck, ftdbb.IOPin(0, "TEST")], debug_mode=True)

    def test_pin_mask(self):
        spi = ftdbb.Port([self.pin_ck], debug_mode=True)
        self.assertEqual(spi.output_pins, 0x1)
        self.assertEqual(spi.input_pins, 0)

        spi = ftdbb.Port([self.pin_rd], debug_mode=True)
        self.assertEqual(spi.output_pins, 0)
        self.assertEqual(spi.input_pins, 4)

        spi = ftdbb.Port([self.pin_lres, self.pin_lcs, self.pin_ck, self.pin_td, self.pin_rd],
                         debug_mode=True)
        self.assertEqual(spi.output_pins, 0x2b)
        self.assertEqual(spi.input_pins, 4)

    def test_open(self):
        with self.assertRaisesRegex(OSError, "Can't open"):
            _ = ftdbb.Port([self.pin_lres, self.pin_lcs, self.pin_ck, self.pin_td, self.pin_rd],
                           debug_mode=False)

    def test_getpin(self):
        spi = ftdbb.Port([self.pin_lres, self.pin_lcs, self.pin_ck, self.pin_td, self.pin_rd],
                         debug_mode=True)
        p = spi.get_pin_object(0)
        self.assertEqual(p, self.pin_ck)
        p = spi.get_pin_object(5)
        self.assertEqual(p, self.pin_lres)
        p = spi.get_pin_object(10)
        self.assertIsNone(p)

    def test_data_send(self):
        spi = ftdbb.Port([self.pin_lres, self.pin_lcs, self.pin_ck, self.pin_td, self.pin_rd],
                         debug_mode=True)
        # After reset, initial value (LRES, LCS, CK, TD) = (1, 1, 0, 0) should be sent
        self.assertEqual(len(spi.signal_history), 1)
        self.assertEqual(spi.signal_history[0], 0x28)

        # Set LCS=0, CK=1 and send.
        self.pin_lcs.value = 0
        self.pin_ck.value = 1
        spi.set_pins()
        self.assertEqual(len(spi.signal_history), 2)
        self.assertEqual(spi.signal_history[1], 0x21)

    def test_data_received(self):
        spi = ftdbb.Port([self.pin_lres, self.pin_lcs, self.pin_ck, self.pin_td, self.pin_rd],
                         debug_mode=True)
        spi._debug_read_data = 0b00000010
        spi.get_pins()
        self.assertEqual(self.pin_rd.value, 0)

        spi._debug_read_data = 0b11111101
        spi.get_pins()
        self.assertEqual(self.pin_rd.value, 1)


if __name__ == "__main__":
    unittest.main()
