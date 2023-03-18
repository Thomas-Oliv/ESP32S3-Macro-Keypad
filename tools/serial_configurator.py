
import sys
from serial.tools.list_ports import comports
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout, QMessageBox
from custom_widgets import *
import pickle

WIDTH = 1000
HEIGHT = 800

# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    
    def __init__(self):
        super(MainWindow, self).__init__()
        #DEFAULT PARAMETERS
        self.num_rows =3
        self.num_cols =3
        self.hwid = '303A:4002'
        self.setMaximumSize(WIDTH, HEIGHT)

        self.data= [[]] * self.num_rows*self.num_cols

        self.setWindowTitle("Keypad Configurator")

        hwid_widget = InputField("Device Hardware Id (HWID)", self.hwid )
        hwid_widget.text_changed.connect(self.__hwid_changed)
        hwid_widget.check_for_device.connect(self.__check_for_device)

        resize_widget = GridResize( self.num_rows, self.num_cols )
        resize_widget.resize_clicked.connect(self.__on_resize)

        self.grid_widget = ButtonGrid(self.num_rows, self.num_cols )
        self.grid_widget.clicked_pos.connect(self.__grid_selected)

        layout = QVBoxLayout()
        layout.addWidget(hwid_widget,stretch=1)
        loadButtons =LoadButtons()
        loadButtons.load_file.connect(self.__load_file)
        loadButtons.load_from_board.connect(self.__load_from_board)
        layout.addWidget(loadButtons,stretch=1)
        layout.addWidget(resize_widget,stretch=1)
        layout.addWidget(self.grid_widget,stretch=6)
        saveButtons = SaveButtons()
        saveButtons.save_file.connect(self.__save_file)
        saveButtons.flash_to_board.connect(self.__flash_to_board)
        layout.addWidget(saveButtons,stretch=1)
        

        self.widget = QWidget()
        self.widget.setLayout(layout)
        self.setCentralWidget(self.widget)

    def __hwid_changed(self, input_str:str):
        self.hwid = input_str

    def __check_for_device(self):
        ports = comports()
        for port_info in ports:
            if self.hwid in port_info.hwid:
                self.__send_alert("Device Information", "Device was successfully found.", QMessageBox.Icon.NoIcon)
                return
        self.__send_alert("Device Information", "Failed to find device.", QMessageBox.Icon.Information)

    def __grid_selected(self, row,col):
        dlg = EditConfigDialog(self.data[row*self.num_cols+col], WIDTH, HEIGHT)
        dlg.resize(WIDTH,HEIGHT)
        if dlg.exec():
            self.__send_alert("Edit Information", "Updated config successfully.", QMessageBox.Icon.Information)
            self.data[row*self.num_cols+col] = dlg.get_data()

    def __on_resize(self, rows,cols):
        temp =[]

        for i in range(rows):
            for j in range(cols):
                if(i < self.num_rows and j < self.num_cols):
                    temp.append(self.data[i*self.num_cols+j])
                else:
                    temp.append([])

        self.data = temp
        self.num_rows = rows
        self.num_cols = cols
        self.grid_widget.set_size(self.num_rows,self.num_cols)
    
    def __send_alert(self,title:str, message:str,  icon):
        dlg = QMessageBox(self)
        dlg.setWindowTitle(title)
        dlg.setText(message)
        dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
        dlg.setIcon(icon)
        dlg.exec()

    def __save_file(self, fname):
        with open(fname, "wb") as file_out:
            pickle.dump(self.data, file_out)
    
    def __flash_to_board(self):
        print("TODO: FLASH -- Serialize and talk over cdc")
    
    def __load_file(self, fname):
        with open(fname, "rb") as file_in:
            self.data = pickle.load(file_in)
    
    def __load_from_board(self):
        print("TODO: LOAD FROM BOARD -- De-Serialize and talk over cdc")

app = QApplication(sys.argv)
window = MainWindow()
window.show()

window.resize(WIDTH,HEIGHT)
app.exec()
