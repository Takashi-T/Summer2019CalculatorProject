# -*- coding: utf-8 -*-
#################################################################
#
# The Calculator Project for Summer 2019.
#
#   The GUI.
#
#
#  Copyright (C) 2019.  Takashi Totsuka. All rights reserved.
##################################################################

from PyQt5.QtWidgets import QApplication, QGridLayout, QVBoxLayout, QHBoxLayout, QSizePolicy,\
    QWidget, QFrame, QLabel, QPushButton, QLineEdit
from PyQt5 import QtCore, QtGui


def _modify_number_font(f, bold=True):
    if bold:
        f.setBold(True)
    pt = f.pointSize()
    if pt < 0:
        raise NotImplementedError("Point size font not supported")
    f.setPointSize(pt * 2)
    return f


class MainPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.clear_callback = None
        self.run_callback = None

        # Create widgets
        mp = QGridLayout(self)

        self.decimal_inputs = DecimalInputData(self._cb_clear_button, self._cb_run_button)
        self.binary_inputs = BinaryInputData()
        self.binary_inputs.set_values(self.decimal_inputs.get_values())

        self.decimal_output = DecimalOutputData()
        self.binary_output = BinaryOutputData()
        self.set_output_value(0, 0)

        self.snapshots = SnapShots()

        r_arrow = QtGui.QPixmap()
        r_arrow.load("arrow-grey3.bmp")
        r_pix = r_arrow.toImage().scaledToWidth(60)
        r_arrow = QtGui.QPixmap(r_pix)
        arrow_mask = r_arrow.createHeuristicMask()
        r_arrow.setMask(arrow_mask)

        l_pix = r_arrow.toImage().mirrored(horizontal=True)
        l_arrow = QtGui.QPixmap(l_pix)
        l_arrow.fromImage(l_pix)

        l1 = QLabel("D to B")
        l1.setPixmap(r_arrow)
        l2 = QLabel("B to R")
        l2.setPixmap(r_arrow)
        l3 = QLabel("R to B")
        l3.setPixmap(l_arrow)
        l4 = QLabel("B to D")
        l4.setPixmap(l_arrow)
        mp.addWidget(self.decimal_inputs, 0, 0, alignment=QtCore.Qt.AlignVCenter)
        mp.addWidget(l1, 0, 1, alignment=QtCore.Qt.AlignVCenter)
        mp.addWidget(self.binary_inputs, 0, 2, alignment=QtCore.Qt.AlignVCenter)
        mp.addWidget(l2, 0, 3)
        mp.addWidget(self.snapshots, 0, 4, 2, 1)
        mp.addWidget(l3, 1, 3)
        mp.addWidget(self.binary_output, 1, 2)
        mp.addWidget(l4, 1, 1)
        mp.addWidget(self.decimal_output, 1, 0)

        # Set row/column stretch
        mp.setRowStretch(0, 5)
        mp.setRowStretch(1, 5)

        mp.setColumnStretch(0, 5)
        mp.setColumnStretch(1, 1)
        mp.setColumnStretch(2, 5)
        mp.setColumnStretch(3, 1)
        mp.setColumnStretch(4, 5)

        self.setLayout(mp)

        self.show()

    def set_clear_callback(self, f):
        self.clear_callback = f

    def set_run_callback(self, f):
        self.run_callback = f

    def set_output_value(self, raw_value_y, value_y):
        self.decimal_output.set_value(value_y)
        self.binary_output.set_value(raw_value_y)

    def set_snapshots(self, l_t, l_v):
        self.snapshots.set_snapshots(l_t, l_v)

    def _cb_clear_button(self):
        # GUI clean up
        self.decimal_inputs.set_values((0, 0))
        self.binary_inputs.set_values((0, 0))
        self.set_output_value(0, 0)

        # Call call back function
        if self.clear_callback is not None:
            self.clear_callback()

    def _cb_run_button(self, is_plus=True):
        # GUI house keeping
        value_a, value_b = self.decimal_inputs.get_values()
        self.binary_inputs.set_values((value_a, value_b))

        # Call call back function
        if self.run_callback is not None:
            self.run_callback(value_a, value_b, is_plus)


class DecimalInputData(QFrame):
    def __init__(self, cbf_clr, cbf_run):
        super().__init__()

        # Store call back functions
        self.cbf_clear = cbf_clr
        self.cbf_run = cbf_run

        # Widgets for the input data A
        label_a = QLabel("Input A")
        dec_input_a = QLineEdit("0")
        dec_input_a.setInputMask("999")  # Acceptable string is [0-9][0-9][0-9] in regexp.
        dec_input_a.setMaximumWidth(100)
        f = dec_input_a.font()
        _modify_number_font(f)
        dec_input_a.setFont(f)

        # Widgets for the input data B
        label_b = QLabel("Input B")
        dec_input_b = QLineEdit("0")
        dec_input_b.setInputMask("999")  # Acceptable string is [0-9][0-9][0-9] in regexp.
        dec_input_b.setMaximumWidth(100)
        f = dec_input_b.font()
        _modify_number_font(f)
        dec_input_b.setFont(f)

        hl = QHBoxLayout()
        btn_clr = QPushButton("CLR")
        btn_clr.clicked.connect(self.cbf_clear)
        btn_clr.setStyleSheet("QPushButton {background:blue; color: white; font: bold 12pt} "
                              "QPushButton:pressed {background:darkblue}")
        sp = QSizePolicy()
        sp.setVerticalPolicy(QSizePolicy.Expanding)
        btn_clr.setSizePolicy(sp)

        btn_add = QPushButton("RUN\n+")
        btn_add.clicked.connect(lambda : self.cbf_run(is_plus=True))
        btn_add.setStyleSheet("QPushButton {background:crimson; color: white; font: bold 12pt} "
                              "QPushButton:pressed {background:darkred}")

        btn_sub = QPushButton("RUN\n-")
        btn_sub.clicked.connect(lambda : self.cbf_run(is_plus=False))
        btn_sub.setStyleSheet("QPushButton {background:crimson; color: white; font: bold 12pt}"
                              "QPushButton:pressed {background:darkred}")
        hl.addWidget(btn_clr)
        hl.addWidget(btn_add)
        hl.addWidget(btn_sub)

        vl = QVBoxLayout()
        vl.addWidget(label_a)
        vl.addWidget(dec_input_a)
        vl.addWidget(label_b)
        vl.addWidget(dec_input_b)
        vl.addLayout(hl)
        self.setLayout(vl)

        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Sunken)
        self.setLineWidth(1)
        self.setMidLineWidth(1)

        self.dec_input_a = dec_input_a
        self.dec_input_b = dec_input_b

    def get_values(self):
        val_a = int(self.dec_input_a.text())
        val_b = int(self.dec_input_b.text())
        return val_a, val_b

    def set_values(self, t_values):
        value_a, value_b = t_values
        value_a &= 0xff
        value_b &= 0xff
        self.dec_input_a.setText("{:d}".format(value_a))
        self.dec_input_b.setText("{:d}".format(value_b))


class BinaryInputData(QFrame):
    def __init__(self):
        super().__init__()

        bin_label_a = QLabel("Input A")
        value_a = QLabel("  10110011")
        f = value_a.font()
        _modify_number_font(f)
        value_a.setFont(f)
        self.value_a = value_a

        bin_label_b = QLabel("Input B")
        value_b = QLabel("  00111011")
        f = value_b.font()
        _modify_number_font(f)
        value_b.setFont(f)
        self.value_b = value_b

        vl = QVBoxLayout()
        vl.addWidget(bin_label_a, alignment=QtCore.Qt.AlignBottom)
        vl.addWidget(value_a, alignment=QtCore.Qt.AlignBottom)
        vl.addWidget(bin_label_b, alignment=QtCore.Qt.AlignTop)
        vl.addWidget(value_b, alignment=QtCore.Qt.AlignTop)
        self.setLayout(vl)

        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Sunken)
        self.setLineWidth(1)
        self.setMidLineWidth(1)

    def set_values(self, t_values):
        value_a, value_b = t_values
        value_a &= 0xff
        value_b &= 0xff
        str_a = "  {:08b}".format(value_a)
        str_b = "  {:08b}".format(value_b)
        self.value_a.setText(str_a)
        self.value_b.setText(str_b)


class DecimalOutputData(QFrame):
    def __init__(self):
        super().__init__()

        dec_label_y = QLabel("Output Y")
        value_y = QLabel("0")
        f = value_y.font()
        _modify_number_font(f)
        value_y.setFont(f)
        self.value_y = value_y

        vl = QVBoxLayout()
        vl.addWidget(dec_label_y, alignment=QtCore.Qt.AlignBottom)
        vl.addWidget(value_y, alignment=QtCore.Qt.AlignTop)

        self.setLayout(vl)
        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Sunken)
        self.setLineWidth(1)
        self.setMidLineWidth(1)

    def set_value(self, value_y):
        # value_y &= 0x1ff
        str_y = "{:d}".format(value_y)
        self.value_y.setText(str_y)


class BinaryOutputData(QFrame):
    def __init__(self):
        super().__init__()

        bin_label_y = QLabel("Output Y")
        value_y = QLabel("11100111")
        f = value_y.font()
        _modify_number_font(f)
        value_y.setFont(f)
        self.value_y = value_y

        vl = QVBoxLayout()
        vl.addWidget(bin_label_y, alignment=QtCore.Qt.AlignBottom)
        vl.addWidget(value_y, alignment=QtCore.Qt.AlignTop)
        self.setLayout(vl)

        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Sunken)
        self.setLineWidth(1)
        self.setMidLineWidth(1)

    def set_value(self, value_y):
        value_y &= 0x1ff
        str_y = "{:09b}".format(value_y)
        self.value_y.setText(str_y)


class SnapShots(QFrame):
    def __init__(self):
        super().__init__()

        gl = QGridLayout()
        tl = QLabel("Time ")
        gl.addWidget(tl, 0, 0)
        vl = QLabel("Value")
        gl.addWidget(vl, 0, 1, alignment=QtCore.Qt.AlignCenter)

        self.l_widget_time = []
        self.l_widget_val = []
        for r in range(1, 11):
            tl = QLabel("{:.3f}  ".format(r * 0.01))
            self.l_widget_time.append(tl)
            gl.addWidget(tl, r, 0)

            vl = QLabel("000000000")
            self.l_widget_val.append(vl)
            f = vl.font()
            _modify_number_font(f, bold=False)
            vl.setFont(f)
            gl.addWidget(vl, r, 1)

        self.setLayout(gl)
        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Sunken)
        self.setLineWidth(1)
        self.setMidLineWidth(2)

    def set_snapshots(self, l_timestamp, l_value):
        n_rows = len(self.l_widget_time)
        n_snapshots = len(l_timestamp)
        step = n_snapshots / n_rows
        print("Snapshot step={}".format(step))
        if step < 1:
            step = 1
        for r in range(n_rows):
            tl = self.l_widget_time[r]
            vl = self.l_widget_val[r]
            ix_snap = int(r * step)
            if r >= len(l_timestamp):
                tl.setText(" ")
                vl.setText(" ")
            else:
                tl.setText("{:.3f}".format(l_timestamp[ix_snap]))
                vl.setText("{:09b}".format(l_value[ix_snap]))


if __name__ == "__main__":
    import sys

    def dummy_clear_cb():
        print("Clear call back is called")

    def dummy_run_cb(a, b, is_plus=True):
        print("Run call back is called A={}, B~{}, OP={}".format(a, b, "ADD" if is_plus else "SUB"))
        # This is a temporary hack
        y = (a + b) if is_plus else (a - b)
        win.set_output_value(y, y)

    app = QApplication(sys.argv)
    win = MainPanel()
    win.set_clear_callback(dummy_clear_cb)
    win.set_run_callback(dummy_run_cb)
    win.show()

    sys.exit(app.exec_())
