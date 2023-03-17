
import sys
from serial.tools.list_ports import comports
from PyQt6.QtWidgets import QApplication,QWidget, QMainWindow,QVBoxLayout, QMessageBox
from custom_widgets import *

# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    
    def __init__(self):
        super(MainWindow, self).__init__()
        #DEFAULT PARAMETERS
        self.num_rows =3
        self.num_cols =3
        self.hwid = '303A:4002'

        # TODO: Replace with proper initialization
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
        layout.addWidget(LoadButtons(),stretch=1)
        layout.addWidget(resize_widget,stretch=1)
        layout.addWidget(self.grid_widget,stretch=6)
        layout.addWidget(SaveButtons(),stretch=1)

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
        dlg = EditConfigDialog(self.data[row*self.num_cols+col])
        if dlg.exec():
            self.__send_alert("Edit Information", "Updated config successfully.", QMessageBox.Icon.Information)

    def __on_resize(self, rows,cols):
        # TODO: RESIZE DATA GRID HERE AS WELL
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

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
