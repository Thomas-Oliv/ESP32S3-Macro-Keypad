from PyQt6.QtCore import Qt, pyqtSlot, QRunnable, QObject
from PyQt6.QtWidgets import  QWidget, QGridLayout, QDialog, QVBoxLayout, QScrollArea
from base_widgets import *
# N x M grid of buttons which relate 1:1 to keypad button
class ButtonGrid(QWidget):
    clicked_pos = pyqtSignal(int,int)

    def __init__(self, rows, cols):
        super().__init__()
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



class GridResize(QWidget):
    resize_clicked = pyqtSignal(int,int)
    def __init__(self, rows, cols ):
        super().__init__()
        self.rows = rows
        self.cols = cols

        self.row_widget = SpinInputField("Rows: ",  self.rows, 10)  
        self.row_widget.value_changed.connect(self.__rows_changed)

        self.col_widget = SpinInputField("Cols: ", self.cols, 10)
        self.col_widget.value_changed.connect(self.__cols_changed)
        
        resize = UIButton("Resize Grid")
        resize.clicked.connect(self.__resize_clicked)

        layout = QHBoxLayout()
        layout.addWidget(self.row_widget)
        layout.addWidget(self.col_widget)
        layout.addWidget(resize)
        self.setLayout(layout)

    def __resize_clicked(self, e):
        self.resize_clicked.emit(self.rows,self.cols)
    
    def __rows_changed(self, e):
        self.rows = e
    def __cols_changed(self, e):
        self.cols = e

    def set_text(self, rows,cols):
        self.rows = rows
        self.cols = cols
        self.row_widget.set_text(rows)
        self.col_widget.set_text(cols)



class EditConfigDialog(QDialog):
    def __init__(self,config_data):
        super().__init__()
        self.setWindowTitle("Edit Config")
        self.setMaximumSize(MAX_W,MAX_H)
        self.resize(MAX_W, MAX_H)

        add_row_buttons = HorizontalButtonGroup("Add Delay", "Add Keystroke")
        add_row_buttons.left_button_click.connect(self.__addDelay)
        add_row_buttons.right_button_click.connect(self.__addInput)

        self.row_scroll = ScrollableRowBox(config_data)
        
        save_cancel_buttons = HorizontalButtonGroup("Save", "Cancel")
        save_cancel_buttons.left_button_click.connect(self.accept)
        save_cancel_buttons.right_button_click.connect(self.reject)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(add_row_buttons,stretch=1)
        self.mainLayout.addWidget(self.row_scroll,stretch=8)
        self.mainLayout.addWidget(save_cancel_buttons,stretch=1)
        self.setLayout(self.mainLayout)

    def __addDelay(self):
        self.row_scroll.get_row_layout().addWidget(ConfigRow(row_data=KeyStroke(0x00,0x01)))

    def __addInput(self):
        self.row_scroll.get_row_layout().addWidget(ConfigRow(row_data=KeyStroke(0x00,0x00)))

    def get_data(self):
        return_data =[]
        for i in range(self.row_scroll.get_row_layout().count()):
            row :ConfigRow = self.row_scroll.get_row_layout().itemAt(i).widget()
            return_data.append(row.get_data())
        return return_data

# create scrollable window to contain all row settings
class ScrollableRowBox(QScrollArea):
    def __init__(self, row_data: list[KeyStroke] ):
        super().__init__()
        row_widget = QWidget()
        self.row_layout = QVBoxLayout()
        self.row_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        for row in row_data:
            self.row_layout.addWidget(ConfigRow(row))
        row_widget.setLayout(self.row_layout)
        self.setWidget(row_widget)
        self.setWidgetResizable(True)

    def get_row_layout(self):
        return self.row_layout

class ConfigRow(QWidget):
    def __init__(self, row_data: KeyStroke):
        super().__init__()
        self.__row_data = row_data
        self.__dropdown_data = get_key_dropdown_values(self.__row_data.modifier)
        layout = QHBoxLayout()

        #display different row based on if user is adding delay or key press
        if(self.__row_data.key_code == delay_code):
            #Delay unit selection
            delay_type = ConfigComboBox("Units",delay_units, self.__row_data.modifier)
            delay_type.index_changed.connect(self.__delay_unit_index_changed)
            layout.addWidget(delay_type,stretch=3)

            #Max delay == 2 Bytes
            delay_field = SpinInputField("Delay",self.__row_data.delay,65535)
            delay_field.value_changed.connect(self.__update_delay)
            layout.addWidget(delay_field,stretch=3)
        
        else:
            #Modifier checkbox configuration
            modifier_checkboxes = ConfigCheckBoxRowGroup(self.__row_data.modifier)
            modifier_checkboxes.modifier_changed.connect(self.__modifier_changed)
            layout.addWidget(modifier_checkboxes,stretch=6)

            #key code drop down menu
            self.keycode_field = ConfigComboBox("Key Code",self.__dropdown_data, self.__row_data.key_code)
            self.keycode_field.index_changed.connect(self.__key_code_index_changed)
            layout.addWidget(self.keycode_field,stretch=3)

        #Delete row button
        delete_btn = UIButton("Delete")
        delete_btn.clicked.connect(self.__delete)
        layout.addWidget(delete_btn,stretch=1)
        self.setLayout(layout)

    def __delete(self):
        self.deleteLater()
        
    def __update_delay(self,val):
        self.__row_data.delay = val

    def __delay_unit_index_changed(self, indx):
        self.__row_data.modifier = indx

    def __key_code_index_changed(self, indx):
        self.__row_data.key_code = self.__dropdown_data[indx][1]

    def __modifier_changed(self, modifier, shift_state_changed):
        self.__row_data.modifier = modifier
        #update dropdown options on shift change
        if (self.__row_data.key_code != delay_code) and shift_state_changed:
            self.__dropdown_data = get_key_dropdown_values(self.__row_data.modifier)
            self.keycode_field.set_data(self.__dropdown_data)

    def get_data(self):
        return self.__row_data
    

class ConfigCheckBoxRowGroup(QWidget):

    modifier_changed = pyqtSignal(int, bool)
    def __init__(self, modifier):
        super().__init__()

        self.__modifier = modifier

        #Create two rows of checkboxes with an equal number of boxes per row
        row_1_layout = QHBoxLayout()
        row_2_layout = QHBoxLayout()
        for i in range(1, len(modifiers)):
            check_box = ConfigCheckBox(modifiers[i][1], self.__modifier & modifiers[i][1] )
            check_box.setChecked(modifiers[i][1] & self.__modifier)
            check_box.id_state_changed.connect(self.__check_box_state_changed)
            check_box.setText(modifiers[i][0])

            if(i < len(modifiers)/2):
                row_1_layout.addWidget(check_box)
            else:
                row_2_layout.addWidget(check_box)

        row_1 = QWidget() 
        row_1.setLayout(row_1_layout)
        row_2 = QWidget()
        row_2.setLayout(row_2_layout)

        layout = QVBoxLayout()
        layout.addWidget(row_1)
        layout.addWidget(row_2)
        self.setLayout(layout)
        
    def __check_box_state_changed(self, state, id):
        if state:
            #set bit
            self.__modifier |= id
        else:
            #clear bit
            self.__modifier &= ~id
        
        self.modifier_changed.emit(self.__modifier, ( id == L_SHIFT or id == R_SHIFT))
    

class WorkerSignals(QObject):
    result = pyqtSignal(object)
    error = pyqtSignal()

class Worker(QRunnable):
    result = pyqtSignal(object)
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(
                *self.args, **self.kwargs
            )
            self.signals.result.emit(result)  # Done
        except:
            self.signals.error.emit()
            
        
