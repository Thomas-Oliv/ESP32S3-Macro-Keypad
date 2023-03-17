import os
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QFileDialog, QLabel,QWidget,QPushButton,QGridLayout, QSizePolicy, QHBoxLayout ,QLineEdit, QSpinBox, QDialog, QDialogButtonBox,QVBoxLayout, QCheckBox,QComboBox
from PyQt6.QtGui import QFont
from usb_hid import *



class ConfigCheckBox(QCheckBox):
    id_state_changed =pyqtSignal(int, int)
    def __init__(self, id):
        super().__init__()
        self.id = id
        self.stateChanged.connect(self.__id_state_changed)

    def __id_state_changed(self,e):
        self.id_state_changed.emit(self.e,id)

class ConfigComboBox(QWidget):
    index_changed = pyqtSignal(int)
    def __init__(self, label: str, data):
        super().__init__()
        label_widget = QLabel(label+":")
        label_widget.setFont(QFont('Times', 15))

        self.input_field = QComboBox()
        self.input_field.setFont(QFont('Times', 15))
        self.set_data(data)
        self.input_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.input_field.currentIndexChanged.connect(self.__index_changed)

        layout = QHBoxLayout()
        layout.addWidget(label_widget)
        layout.addWidget(self.input_field)
        self.set_data(data)


    def set_data(self, data):
        for i in reversed(range(self.input_field.count())): 
            self.input_field.removeItem(i)
        for name, id in data:
            self.input_field.addItem(name,id)

            
    def __index_changed(self, e):
        self.value_changed.emit(e)
    

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

class SpinInputField(QWidget):
    value_changed = pyqtSignal(int)
    def __init__(self, label: str, default_value:int):
        super(SpinInputField, self).__init__()
        label_widget = QLabel(label+":")
        label_widget.setFont(QFont('Times', 15))

        input_field = QSpinBox()
        input_field.setFont(QFont('Times', 15))
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


class ButtonGrid(QWidget):
    clicked_pos = pyqtSignal(int,int)

    def __init__(self, rows, cols):
        super(ButtonGrid, self).__init__()
        grid_layout = QGridLayout()
        self.setLayout(grid_layout)
        self.__add_buttons(rows,cols)

    def set_size(self,num_rows, num_cols):

        # remove old buttons
        for i in reversed(range(self.layout().count())): 
            self.layout().itemAt(i).widget().deleteLater()
        # add new buttons
        self.__add_buttons(num_rows,num_cols)
        
    def __add_buttons(self, rows, cols):
        self.num_rows = rows
        self.num_cols = cols
        for i in range(self.num_rows):
            for j in range(self.num_cols):
                button = GridButton("Binding ("+str(i)+","+str(j)+")", i, j)
                button.clicked_pos.connect(self.__clicked_pos)
                self.layout().addWidget(button, i, j)

     # On click we return pos
    def __clicked_pos(self, rows,cols):
        self.clicked_pos.emit(rows, cols)

class LoadButtons(QWidget):
    load_file = pyqtSignal(str)
    load_from_board = pyqtSignal()
    def __init__(self):
        super(LoadButtons,self).__init__()
        button_load_from_file = UIButton("Load From File")
        button_load_from_file.clicked.connect(self.__load_file)
        button_load_from_board = UIButton("Load From Board")
        button_load_from_board.clicked.connect(self.__load_from_board)

        layout = QHBoxLayout()
        layout.addWidget(button_load_from_file)
        layout.addWidget(button_load_from_board)
        self.setLayout(layout)

    def __load_file(self, e):
        fname  = QFileDialog.getOpenFileName(
            self,
            caption="Open File",
            filter="Binary Files (*.bin)",
        )[0]
        if fname and fname.endswith(".bin") and os.path.exists(fname):
            self.load_file.emit(fname)
        else:
            print("file does not exists\r\n")
    
    def __load_from_board(self):
        print("TODO: Load from board\r\n")
        self.load_from_board.emit()


class SaveButtons(QWidget):
    save_file = pyqtSignal(str)
    flash_to_board = pyqtSignal()
    def __init__(self ):
        super(SaveButtons,self).__init__()
        button_save_to_file = UIButton("Save To File")  
        button_save_to_file.clicked.connect(self.__save_file)
        button_flash_to_board = UIButton("Flash To Board")
        button_flash_to_board.clicked.connect(self.__load_from_board)
        layout = QHBoxLayout()
        layout.addWidget(button_save_to_file)
        layout.addWidget(button_flash_to_board)
        self.setLayout(layout)

    def __save_file(self, e):
        fname  = QFileDialog.getSaveFileName(
            self,
            caption="Open File",
            filter="Binary Files (*.bin)",
        )[0]
        if fname and fname.endswith(".bin") and os.path.isdir(os.path.dirname(fname)):
            self.save_file.emit(fname)
        else:
            print("Path to file doesn't exist\r\n")
    
    def __load_from_board(self):
        print("TODO: flash to board\r\n")
        self.flash_to_board.emit()

class GridResize(QWidget):
    resize_clicked = pyqtSignal(int,int)
    def __init__(self, rows,cols ):
        super(GridResize,self).__init__()
        self.num_rows = rows
        self.num_cols = cols

        num_rows = SpinInputField("Rows: ",  self.num_rows)  
        num_rows.value_changed.connect(self.__rows_changed)

        num_cols = SpinInputField("Cols: ", self.num_cols)
        num_cols.value_changed.connect(self.__cols_changed)
        
        resize = UIButton("Resize Grid")
        resize.clicked.connect(self.__resize_clicked)

        layout = QHBoxLayout()
        layout.addWidget(num_rows)
        layout.addWidget(num_cols)
        layout.addWidget(resize)
        self.setLayout(layout)

    def __resize_clicked(self, e):
        self.resize_clicked.emit(self.num_rows,self.num_cols)
    
    def __rows_changed(self, e):
        self.num_rows = e
    def __cols_changed(self, e):
        self.num_cols = e


class ConfigRow(QWidget):
    def __init__(self, row_data: key_stroke):
        super().__init__()
        self.row_data = row_data
        self.dropdown_data =GetKeyDropDownValues(shifted(self.row_data.key_code))
        layout =QHBoxLayout()
        for mod in modifiers[1:]:
            check_box = ConfigCheckBox()
            check_box.setCheckState(Qt.CheckState.Checked if row_data.modifier & mod[1] else Qt.CheckState.Unchecked)
            check_box.id_state_changed.connect(self.__check_box_state_changed)
            check_box.setText(mod[0])
            layout.addWidget(check_box)

        if(row_data.key_code == delay_code ):
            delay_field = SpinInputField("Delay (ms)",row_data.delay)
            delay_field.value_changed.connect(self.__update_delay)
            layout.addWidget(delay_field)
        else:
            keycode_field = ConfigComboBox("Key Code",self.dropdown_data)
            keycode_field.index_changed.connect(self.__index_changed)
            layout.addWidget(keycode_field)

        delete_btn = UIButton("Delete")
        delete_btn.clicked.connect(self.__delete)

    def __delete(self):
        self.deleteLater()
        
    def __update_delay(self,val):
        self.row_data.delay = val
    def __index_changed(self, indx):
        self.row_data.key_code = self.dropdown_data[indx][1]

    def __check_box_state_changed(self, state, id):
        if state:
            #set bit
            self.row_data.key_code |= modifiers[id][1]
        else:
            #clear bit
            self.row_data.key_code &= ~modifiers[id][1]
        
        self.dropdown_data =GetKeyDropDownValues(shifted(self.row_data.key_code))
            



class EditConfigDialog(QDialog):
    def __init__(self,config_data, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()

        self.setWindowTitle("Edit")
        #TODO: print out rows
        for row in config_data:
            self.layout.addWidget(ConfigRow(row))


        QBtn = QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
