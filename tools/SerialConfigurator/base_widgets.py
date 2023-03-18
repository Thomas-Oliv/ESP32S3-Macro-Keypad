import os
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel,QWidget,QPushButton, QSizePolicy, QHBoxLayout ,QLineEdit, QSpinBox, QCheckBox, QComboBox
from PyQt6.QtGui import QFont
from usb_hid import *

MAX_W = 1000
MAX_H = 800

# Horizontal button group with two buttons
class HorizontalButtonGroup(QWidget):
    left_button_click = pyqtSignal()
    right_button_click= pyqtSignal()
    def __init__(self, label_left, label_right ):
        super().__init__()
        button_layout = QHBoxLayout()
        left_button = UIButton(label_left)
        left_button.clicked.connect(self.__left_button_click)
        right_button = UIButton(label_right)
        right_button.clicked.connect(self.__right_button_click)

        button_layout.addWidget(left_button)
        button_layout.addWidget(right_button)
        self.setLayout(button_layout)

    def __left_button_click(self):
        self.left_button_click.emit()
    
    def __right_button_click(self):
        self.right_button_click.emit()

class SpinInputField(QWidget):
    value_changed = pyqtSignal(int)
    def __init__(self, label: str, default_value:int, max_val):
        super().__init__()
        label_widget = QLabel(label+":")
        label_widget.setFont(QFont('Times', 15))

        self.input_field = QSpinBox()
        self.input_field.setFont(QFont('Times', 15))
        self.input_field.setMinimum(0)
        self.input_field.setMaximum(max_val)
        self.input_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.set_text(default_value)
        self.input_field.valueChanged.connect(self.__value_changed)

        layout = QHBoxLayout()
        layout.addWidget(label_widget)
        layout.addWidget(self.input_field)
        self.setLayout(layout)

    def __value_changed(self, e):
        self.value_changed.emit(e)

    def set_text(self,value):
        self.input_field.setValue(value)

class InputField(QWidget):
    text_changed = pyqtSignal(str)
    check_for_device = pyqtSignal()
    def __init__(self, label: str, default_val:str):
        super().__init__()
        label_widget = QLabel(label+":")
        label_widget.setFont(QFont('Times', 15))

        self.input_field = QLineEdit()
        self.input_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.input_field.setFont(QFont('Times', 15))
        self.set_text(default_val)
        self.input_field.setPlaceholderText("Value of "+label)
        self.input_field.textChanged.connect(self.__text_changed)

        button = UIButton("Check For Device")
        button.clicked.connect(self.__check_for_device)

        layout = QHBoxLayout()
        layout.addWidget(label_widget)
        layout.addWidget(self.input_field)
        layout.addWidget(button)
        self.setLayout(layout)

    def __check_for_device(self):
        self.check_for_device.emit()
            
    def __text_changed(self, e):
        self.text_changed.emit(e)

    def set_text(self, value):
        self.input_field.setText(value)


class ConfigComboBox(QWidget):
    index_changed = pyqtSignal(int)
    def __init__(self, label: str, data :list[(str,int)], default_code):
        super().__init__()
        label_widget = QLabel(label+":")
        label_widget.setFont(QFont('Times', 15))

        self.input_field = QComboBox()
        self.input_field.setFont(QFont('Times', 15))
        self.input_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.input_field.currentIndexChanged.connect(self.__index_changed)

        layout = QHBoxLayout()
        layout.addWidget(label_widget)
        layout.addWidget(self.input_field)

        self.set_data(data)
        for indx, val in enumerate(data):
            if val[1] == default_code:
                self.input_field.setCurrentIndex(indx)

        self.setLayout(layout)

    def set_data(self, data):
        #clear old items
        for i in reversed(range(self.input_field.count())): 
            self.input_field.removeItem(i)
        #add new items
        for name, id in data:
            self.input_field.addItem(name,id)

            
    def __index_changed(self, e):
        self.index_changed.emit(e)


class ConfigCheckBox(QCheckBox):
    id_state_changed =pyqtSignal(int, int)
    def __init__(self, id, is_checked):
        super().__init__()
        self.id = id
        self.stateChanged.connect(self.__id_state_changed)
        self.setChecked(is_checked)

    def __id_state_changed(self,e):
        self.id_state_changed.emit(e,self.id)

class GridButton(QPushButton):
    clicked_pos = pyqtSignal(int,int)
    def __init__(self, label:str, x_pos:int, y_pos:int):
        super().__init__(label) 
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setFont(QFont('Times', 15))
        self.clicked.connect(self.__clicked_pos)
    # On click we return pos
    def __clicked_pos(self, e):
        self.clicked_pos.emit(self.x_pos, self.y_pos)



class UIButton(QPushButton):
    def __init__(self, label:str):
        super().__init__(label)  
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setFont(QFont('Times', 15))

