import os
from PyQt6.QtCore import pyqtSignal, Qt,QEvent
from PyQt6.QtWidgets import QFileDialog, QLabel,QWidget,QPushButton,QGridLayout, QSizePolicy, QHBoxLayout ,QLineEdit, QSpinBox, QDialog, QDialogButtonBox,QVBoxLayout, QCheckBox,QComboBox, QListWidget, QListWidgetItem
from PyQt6.QtGui import QFont,QStandardItemModel
from usb_hid import *

#TODO: CHECKBOX SAVE VALUE,

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
        #set to default position
        self.input_field.setCurrentIndex(0)

            
    def __index_changed(self, e):
        self.index_changed.emit(e)
    

class GridButton(QPushButton):
    clicked_pos = pyqtSignal(int,int)
    def __init__(self, label:str, x_pos:int, y_pos:int):
        super(GridButton, self).__init__(label) 
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
        super(UIButton, self).__init__(label)  
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setFont(QFont('Times', 15))

    
class ConfigCheckBox(QCheckBox):
    id_state_changed =pyqtSignal(int, int)
    def __init__(self, id, is_checked):
        super().__init__()
        self.id = id
        self.stateChanged.connect(self.__id_state_changed)
        self.setChecked(is_checked)

    def __id_state_changed(self,e):
        self.id_state_changed.emit(e,self.id)



class SpinInputField(QWidget):
    value_changed = pyqtSignal(int)
    def __init__(self, label: str, default_value:int, max_val):
        super(SpinInputField, self).__init__()
        label_widget = QLabel(label+":")
        label_widget.setFont(QFont('Times', 15))

        input_field = QSpinBox()
        input_field.setFont(QFont('Times', 15))
        input_field.setMinimum(0)
        input_field.setMaximum(max_val)
        input_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        input_field.setValue(default_value)
        input_field.valueChanged.connect(self._value_changed)

        layout = QHBoxLayout()
        layout.addWidget(label_widget)
        layout.addWidget(input_field)
        self.setLayout(layout)

    def _value_changed(self, e):
        self.value_changed.emit(e)

class InputField(QWidget):
    text_changed = pyqtSignal(str)
    check_for_device = pyqtSignal()
    def __init__(self, label: str, default_value:str):
        super(InputField,self).__init__()
        label_widget = QLabel(label+":")
        label_widget.setFont(QFont('Times', 15))

        input_field = QLineEdit()
        input_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        input_field.setText(default_value)
        input_field.setFont(QFont('Times', 15))
        input_field.setPlaceholderText("Value of "+label)
        input_field.textChanged.connect(self.__text_changed)

        button = UIButton("Check For Device")
        button.clicked.connect(self.__check_for_device)

        layout = QHBoxLayout()
        layout.addWidget(label_widget)
        layout.addWidget(input_field)
        layout.addWidget(button)
        self.setLayout(layout)

    def __check_for_device(self):
        self.check_for_device.emit()
            
    def __text_changed(self, e):
        self.text_changed.emit(e)
