# Summer2019CalculatorProject
Summer Vacation 2019 Project with my daughter to create a relay based 8bit ALU. This is the GUI part.

For the science class project, my 11-year daughter is going to create an 8 bits adder using electro-magnetic relays as the logic device.

This python code is the GUI and communication interface to feed two 8-bit inputs and display the 9-bit (8 bits with carry) result on a host computer.

* The host talks to the target hardware (the adder) via USB.
* FTDI's FT232H device is on the target hardware which serves as a remote controlled GPIO device which controles two serial-parallel shift registers for input data and one parallel-serial shift register for the sum.
