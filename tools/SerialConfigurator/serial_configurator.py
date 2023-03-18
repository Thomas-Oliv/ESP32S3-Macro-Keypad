
import sys
from serial.tools.list_ports import comports
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout, QMessageBox, QFileDialog
from custom_widgets import *
import pickle
from crc import Calculator, Crc16
import serial
from struct import pack, unpack

# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    
    def __init__(self):
        super(MainWindow, self).__init__()
        #DEFAULT PARAMETERS

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
        self.__send_alert("Device Information", "Failed to find device.", QMessageBox.Icon.Information)

    def __grid_selected(self, row,col):
        dlg = EditConfigDialog(self.device.data[row*self.device.cols + col])
        if dlg.exec():
            self.__send_alert("Edit Information", "Updated config successfully.", QMessageBox.Icon.Information)
            self.device.data[row*self.device.cols + col] = dlg.get_data()

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
    
    #Create a little popup with a given message and icon
    def __send_alert(self,title:str, message:str,  icon):
        dlg = QMessageBox(self)
        dlg.setWindowTitle(title)
        dlg.setText(message)
        dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
        dlg.setIcon(icon)
        dlg.exec()

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
                calculator = Calculator(Crc16.CCITT)
                packed_obj, total_size = serialize_data(self.device.data)
                crc = calculator.checksum(packed_obj)
                with serial.Serial(port= port_info.device) as s:
                    sync_msg = pack("<BBLH",0xFF,0x01,total_size,crc)
                    s.write(sync_msg)
                    # expect sync to be echo'd
                    res = s.read(8)
                    if(res == sync_msg):
                        s.write(packed_obj)
                        # expect calculated crc on board to match
                        res = s.read(2)
                        if( unpack("<H",res) == crc):
                            self.__send_alert("Flash Status", "Device was successfully flashed.", QMessageBox.Icon.NoIcon)
                        else:
                            self.__send_alert("Flash Status", "Something went wrong when flashing device.", QMessageBox.Icon.Warning)
                    else:
                        self.__send_alert("Flash Status", "Something went wrong when flashing device.", QMessageBox.Icon.Warning)
                return
        self.__send_alert("Flash Status", "Failed to find device.", QMessageBox.Icon.Information)
    
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
                with serial.Serial(port= port_info.device) as s:
                    sync_msg = pack("<BB",0xFF,0x10)
                    s.write(sync_msg)
                    # expect sync to be echo'd but add crc and length expected to be returned
                    res = s.read(8)
                    _, length, crc_expected = unpack("<HLH",res)
                    if(res[0:2] == sync_msg[0:2]):
                        packed_obj = s.read(length)
                        calculator = Calculator(Crc16.CCITT)
                        crc_calc = calculator.checksum(packed_obj)
                        if(crc_calc == crc_expected):
                            self.device.data = deserialize_data(packed_obj)
                            self.update_ui()
                            self.__send_alert("Flash Status", "Device was successfully read.", QMessageBox.Icon.NoIcon)
                        else:
                             self.__send_alert("Load Status", "Something went wrong when reading from device.", QMessageBox.Icon.Warning)
                    else:
                        self.__send_alert("Load Status", "Something went wrong when reading from device.", QMessageBox.Icon.Warning)
                return
        self.__send_alert("Load Status", "Failed to find device.", QMessageBox.Icon.Information)

    #update ui elements on load
    def update_ui(self):
        self.hwid_widget.set_text(self.device.hwid)
        self.resize_widget.set_text(self.device.rows,self.device.cols )
        self.grid_widget.set_size(self.device.rows ,self.device.cols)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()


