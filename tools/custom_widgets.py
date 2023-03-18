import os
from PyQt6.QtCore import pyqtSignal,QSize
from PyQt6.QtWidgets import QFileDialog,QWidget,QGridLayout, QHBoxLayout , QDialog, QDialogButtonBox,QVBoxLayout, QScrollArea
from usb_hid import *
from base_widgets import *




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

    def __save_file(self):
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
        self.flash_to_board.emit()

class GridResize(QWidget):
    resize_clicked = pyqtSignal(int,int)
    def __init__(self, rows,cols ):
        super(GridResize,self).__init__()
        self.num_rows = rows
        self.num_cols = cols

        num_rows = SpinInputField("Rows: ",  self.num_rows,15)  
        num_rows.value_changed.connect(self.__rows_changed)

        num_cols = SpinInputField("Cols: ", self.num_cols, 15)
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
        layout = QHBoxLayout()
        
        combo_menu = QWidget()
        combo_menu_layout = QVBoxLayout()

        row_1 = QWidget()
        row_2 = QWidget()

        row_1_layout = QHBoxLayout()
        row_2_layout = QHBoxLayout()
        for i in range(1, len(modifiers)):
            check_box = ConfigCheckBox(modifiers[i][1], self.row_data.modifier & modifiers[i][1] )
            check_box.setChecked(modifiers[i][1] & self.row_data.modifier)
            check_box.id_state_changed.connect(self.__check_box_state_changed)
            check_box.setText(modifiers[i][0])
            if(i < len(modifiers)/2):
                row_1_layout.addWidget(check_box)
            else:
                row_2_layout.addWidget(check_box)
        row_1.setLayout(row_1_layout)
        row_2.setLayout(row_2_layout)

        combo_menu_layout.addWidget(row_1)
        combo_menu_layout.addWidget(row_2)
        combo_menu.setLayout(combo_menu_layout)


        layout.addWidget(combo_menu,stretch=6)


        if(self.row_data.key_code == delay_code ):
            delay_field = SpinInputField("Delay (ms)",self.row_data.delay,65535)
            delay_field.value_changed.connect(self.__update_delay)
            layout.addWidget(delay_field,stretch=3)
        else:
            self.keycode_field = ConfigComboBox("Key Code",self.dropdown_data, self.row_data.key_code)
            self.keycode_field.index_changed.connect(self.__index_changed)
            layout.addWidget(self.keycode_field,stretch=3)

        delete_btn = UIButton("Delete")
        delete_btn.clicked.connect(self.__delete)
        layout.addWidget(delete_btn,stretch=1)
        self.setLayout(layout)

    def __delete(self):
        self.deleteLater()
        
    def __update_delay(self,val):
        self.row_data.delay = val

    def __index_changed(self, indx):
        self.row_data.key_code = self.dropdown_data[indx][1]

    def __check_box_state_changed(self, state, id):
        if state:
            #set bit
            self.row_data.modifier |= id
        else:
            #clear bit
            self.row_data.modifier &= ~id

        #update dropdown options on shift change
        if (self.row_data.key_code != delay_code) and ( id == 0x02 or id == 0x20):
            self.dropdown_data= GetKeyDropDownValues(shifted(self.row_data.key_code))
            self.keycode_field.set_data(self.dropdown_data)

    def get_data(self):
        return self.row_data
    

    
class SaveConfigButtons(QWidget):
    save = pyqtSignal()
    cancel = pyqtSignal()
    def __init__(self ):
        super().__init__()
        button_save= UIButton("Save")  
        button_save.clicked.connect(self.__save)
        button_cancel = UIButton("Cancel")
        button_cancel.clicked.connect(self.__cancel)
        layout = QHBoxLayout()
        layout.addWidget(button_save)
        layout.addWidget(button_cancel)
        self.setLayout(layout)

    def __save(self):
        self.save.emit()
    
    def __cancel(self):
        self.cancel.emit()


class EditConfigDialog(QDialog):
    def __init__(self,config_data, max_w , max_h):
        super().__init__()
        self.setWindowTitle("Edit")
        self.setMaximumSize(max_w,max_h)
        self.resize(max_w,max_h)

        row_scroll = QScrollArea()
        self.rowWidget = QWidget()
        rowLayout = QVBoxLayout()
        rowLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        for row in config_data:
            rowLayout.addWidget(ConfigRow(row))
        self.rowWidget.setLayout(rowLayout)
        row_scroll.setWidget(self.rowWidget)
        row_scroll.setWidgetResizable(True)

        buttonWidget = QWidget()
        buttonWidget.resize(QSize(int(max_w/2),int(max_h/16)))
        buttonLayout = QHBoxLayout()
        addDelayButton = UIButton("Add Delay")
        addDelayButton.clicked.connect(self.__addDelay)
        addKeyCodeButton = UIButton("Add Keystroke")
        addKeyCodeButton.clicked.connect(self.__addInput)

        buttonLayout.addWidget(addDelayButton)
        buttonLayout.addWidget(addKeyCodeButton)
        buttonWidget.setLayout(buttonLayout)

        saveButtons = SaveConfigButtons()
        saveButtons.save.connect(self.accept)
        saveButtons.cancel.connect(self.reject)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(buttonWidget,stretch=1)
        self.mainLayout.addWidget(row_scroll,stretch=8)
        self.mainLayout.addWidget(saveButtons,stretch=1)
        self.setLayout(self.mainLayout)

    def __addDelay(self):
        self.rowWidget.layout().addWidget(ConfigRow(row_data=key_stroke(0x00,0x01)))

    def __addInput(self):
        self.rowWidget.layout().addWidget(ConfigRow(row_data=key_stroke(0x00,0x00)))

    def get_data(self):
        return_data =[]
        for i in range(self.rowWidget.layout().count()):
            row = self.rowWidget.layout().itemAt(i).widget()
            return_data.append(row.get_data())
        return return_data