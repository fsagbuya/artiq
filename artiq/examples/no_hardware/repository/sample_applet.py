from PyQt5 import QtWidgets, QtCore, QtGui

from artiq.applets.simple import SimpleApplet
from artiq.gui.entries import procdesc_to_entry

from collections import OrderedDict


class QResponsiveLCDNumber(QtWidgets.QLCDNumber):
    doubleClicked = QtCore.pyqtSignal()

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()


class QCancellableLineEdit(QtWidgets.QLineEdit):
    editCancelled = QtCore.pyqtSignal()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.editCancelled.emit()
        else:
            super().keyPressEvent(event)


class NumberWidget(QtWidgets.QWidget):
    def __init__(self, args, ctl):
        QtWidgets.QWidget.__init__(self)
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.dataset_name = args.dataset
        self.ctl = ctl

        self.stack = QtWidgets.QStackedWidget()
        self.layout.addWidget(self.stack)

        self.lcd_widget = QResponsiveLCDNumber()
        self.lcd_widget.setDigitCount(args.digit_count)
        self.lcd_widget.doubleClicked.connect(self.start_edit)
        self.stack.addWidget(self.lcd_widget)

        self.edit_widget = QCancellableLineEdit()
        self.edit_widget.setValidator(QtGui.QDoubleValidator())
        self.edit_widget.setAlignment(QtCore.Qt.AlignRight)
        self.edit_widget.editCancelled.connect(self.cancel_edit)
        self.edit_widget.returnPressed.connect(self.confirm_edit)
        self.stack.addWidget(self.edit_widget)

        font = QtGui.QFont()
        font.setPointSize(60)
        self.edit_widget.setFont(font)

        self.stack.setCurrentWidget(self.lcd_widget)

        #Entry point
        arguments = OrderedDict([
            ("string", {"desc": {"default": "Hello World", "ty": "StringValue"}, "group": None, "state": "Hello World", "tooltip": None}),
            ("boolean", {"desc": {"default": True, "ty": "BooleanValue"}, "group": "Group", "state": True, "tooltip": None}),
            ("enum", {"desc": {"choices": ["foo", "bar", "quux"], "default": "foo", "ty": "EnumerationValue"}, "group": "Group", "state": "foo", "tooltip": None}),
            ("integer", {"desc": {"default": 42, "max": None, "min": None, "precision": 0, "scale": 1.0, "step": 1, "ty": "NumberValue", "type": "auto", "unit": ""}, "group": None, "state": 42, "tooltip": None}),
            ("float", {"desc": {"default": 4.2e-05, "max": None, "min": None, "precision": 4, "scale": 1e-06, "step": 1e-07, "ty": "NumberValue", "type": "auto", "unit": "us"}, "group": None, "state": 4.2e-05, "tooltip": None}),
            ("scan", {"desc": {"default": [{"repetitions": 1, "ty": "NoScan", "value": 325}], "global_max": 400, "global_min": None, "global_step": 0.1, "precision": 6, "scale": 1.0, "ty": "Scannable", "unit": ""}, "group": None, "state": {"CenterScan": {"center": 0.0, "randomize": False, "seed": None, "span": 100.0, "step": 10.0}, "ExplicitScan": {"sequence": []}, "NoScan": {"repetitions": 1, "value": 325.0}, "RangeScan": {"npoints": 10, "randomize": False, "seed": None, "start": 0.0, "stop": 100.0}, "selected": "NoScan"}, "tooltip": None})
        ])

        grid_layout = QtWidgets.QGridLayout()

        # Loop through arguments to create the widgets
        self._arg_to_widgets = {}
        row = 0
        for name, argument in arguments.items():
            widgets = {}
            self._arg_to_widgets[name] = widgets

            entry_class = procdesc_to_entry(argument["desc"])
            entry = entry_class(argument)
            widgets["entry"] = entry

            widget_item = QtWidgets.QLabel(name)
            widgets["widget_item"] = widget_item

            grid_layout.addWidget(widget_item, row, 0)
            grid_layout.addWidget(entry, row, 1)

            row += 1

        self.layout.addLayout(grid_layout)


    def start_edit(self):
        # QLCDNumber value property contains the value of zero
        # if the displayed value is not a number.
        self.edit_widget.setText(str(self.lcd_widget.value()))
        self.edit_widget.selectAll()
        self.edit_widget.setFocus()
        self.stack.setCurrentWidget(self.edit_widget)

    def confirm_edit(self):
        value = float(self.edit_widget.text())
        self.ctl.set_dataset(self.dataset_name, value)
        self.stack.setCurrentWidget(self.lcd_widget)

    def cancel_edit(self):
        self.stack.setCurrentWidget(self.lcd_widget)

    def data_changed(self, value, metadata, persist, mods):
        try:
            n = float(value[self.dataset_name])
        except (KeyError, ValueError, TypeError):
            n = "---"
        self.lcd_widget.display(n)


def main():
    applet = SimpleApplet(NumberWidget)
    applet.add_dataset("dataset", "dataset to show")
    applet.argparser.add_argument("--digit-count", type=int, default=10,
                                  help="total number of digits to show")
    applet.run()

if __name__ == "__main__":
    main()
