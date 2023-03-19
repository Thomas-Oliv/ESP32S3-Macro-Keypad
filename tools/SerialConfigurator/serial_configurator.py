import os
import sys
from serial.tools.list_ports import comports
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout, QMessageBox, QFileDialog
from custom_widgets import *
from PyQt6.QtCore import QThreadPool
import pickle

# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    
    def __init__(self):
        super(MainWindow, self).__init__()
        #DEFAULT PARAMETERS
        self.threadpool = QThreadPool()
        self.device = Device('303A:4002', 3 ,3)

        self.setWindowTitle("Keypad Configurator")
        self.setMaximumSize(MAX_W, MAX_H)
        self.resize(MAX_W,MAX_H)

        self.hwid_widget = InputField("Device Hardware Id (HWID)", self.device.hwid )
        self.hwid_widget.text_changed.connect(self.__hwid_changed)
        self.hwid_widget.check_for_device.connect(self.__check_for_device)

        loadButtons = HorizontalButtonGroup("Load From File", "Load From Board")
        loadButtons.left_button_click.connect(self.__load_file)
        loadButtons.right_button_click.connect(self.__load_from_board)

        self.resize_widget = GridResize( self.device.rows, self.device.cols )
        self.resize_widget.resize_clicked.connect(self.__on_resize)

        self.grid_widget = ButtonGrid(self.device.rows, self.device.cols )
        self.grid_widget.clicked_pos.connect(self.__grid_selected)

        saveButtons = HorizontalButtonGroup("Save To File", "Flash To Board")
        saveButtons.left_button_click.connect(self.__save_file)
        saveButtons.right_button_click.connect(self.__flash_to_board)

        layout = QVBoxLayout()
        layout.addWidget(self.hwid_widget,stretch=1)
        layout.addWidget(loadButtons,stretch=1)
        layout.addWidget(self.resize_widget,stretch=1)
        layout.addWidget(self.grid_widget,stretch=6)
        layout.addWidget(saveButtons,stretch=1)
        
        self.widget = QWidget()
        self.widget.setLayout(layout)
        self.setCentralWidget(self.widget)

    def __hwid_changed(self, input_str:str):
        self.device.hwid = input_str

    #validate if device is connected or not
    def __check_for_device(self):
        ports = comports()
        for port_info in ports:
            if self.device.hwid in port_info.hwid:
                self.__send_alert("Device Information", "Device was successfully found.", QMessageBox.Icon.NoIcon)
                return
        self.__board_error()

    
    #resize n x m button grid
    def __on_resize(self, rows,cols):
        temp =[]
        #copy data to new grid of size row x col
        for i in range(rows):
            for j in range(cols):
                if(i < self.device.rows and j < self.device.cols):
                    temp.append(self.device.data[i*self.device.cols+j])
                else:
                    temp.append([])
        #update data and dimensions then redraw grid
        self.device.data = temp
        self.device.rows = rows
        self.device.cols = cols
        self.grid_widget.set_size(self.device.rows ,self.device.cols)

    def __grid_selected(self, row,col):
        dlg = EditConfigDialog(self.device.data[row*self.device.cols + col])
        if dlg.exec():
            self.device.data[row*self.device.cols + col] = dlg.get_data()
            self.__send_alert("Edit Information", "Updated config successfully.", QMessageBox.Icon.Information)
    
    #save file action
    def __save_file(self):
        fname  = QFileDialog.getSaveFileName(
            self,
            caption="Open File",
            filter="Pickle Files (*.pickle)",
        )[0]
        if fname and fname.endswith(".pickle") and os.path.isdir(os.path.dirname(fname)):
            with open(fname, "wb") as file_out:
                pickle.dump(self.device, file_out)
        else:
            self.__send_alert("File Information", "File does not exist.", QMessageBox.Icon.Warning)
    
    #TODO: TEST
    def __flash_to_board(self):
        ports = comports()
        for port_info in ports:
            if self.device.hwid in port_info.hwid:
                worker = Worker(flash, port_info.device, self.device)
                worker.signals.result.connect(self.__flash_complete)
                worker.signals.error.connect(self.__flash_error)
                self.threadpool.start(worker)
                #TODO: Disable UI WHILE FLASHING
                return
        self.__board_error()


    def __load_file(self):
        fname  = QFileDialog.getOpenFileName(
            self,
            caption="Open File",
            filter="Pickle Files (*.pickle)",
        )[0]
        if fname and fname.endswith(".pickle") and os.path.exists(fname):
            with open(fname, "rb") as file_in:
                self.device = pickle.load(file_in)
                self.update_ui()
        else:
            self.__send_alert("File Information", "File does not exist.", QMessageBox.Icon.Warning)
    

    #TODO: TEST
    def __load_from_board(self):
        ports = comports()
        for port_info in ports:
            if self.device.hwid in port_info.hwid:
                worker = Worker(load, port_info.device)
                worker.signals.result.connect(self.__load_complete)
                worker.signals.error.connect(self.__load_error)
                self.threadpool.start(worker)
                #TODO: Disable UI WHILE LOADING
                return
        self.__board_error()

    #update ui elements on load
    def update_ui(self):
        self.hwid_widget.set_text(self.device.hwid)
        self.resize_widget.set_text(self.device.rows,self.device.cols )
        self.grid_widget.set_size(self.device.rows ,self.device.cols)

    def __flash_complete(self, is_success):
        if is_success:
            self.__send_alert("Flash Status", "Device was successfully flashed.", QMessageBox.Icon.NoIcon)
        else:
            self.__flash_error()
    
    def __load_complete(self, result):
        data, rows, cols = result
        if(rows > 0 and cols > 0):
            self.device.data = data
            self.device.rows = rows
            self.device.cols = cols
            self.update_ui()
        else:
            self.__load_error()

        #Create a little popup with a given message and icon
    def __send_alert(self,title:str, message:str,  icon):
        dlg = QMessageBox(self)
        dlg.setWindowTitle(title)
        dlg.setText(message)
        dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
        dlg.setIcon(icon)
        dlg.exec()
    
    def __flash_error(self):
         self.__send_alert("Flash Status", "Something went wrong when flashing device.", QMessageBox.Icon.Warning)

    def __load_error(self):
         self.__send_alert("Flash Status", "Something went wrong when loading from device.", QMessageBox.Icon.Warning)

    def __board_error(self):
        self.__send_alert("Device Information", "Failed to find device.", QMessageBox.Icon.Information)


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()


