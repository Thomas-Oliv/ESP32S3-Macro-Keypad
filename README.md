# ESP32-S3 Macro Keypad
Supported Targets:  ESP32-S3

Developed on: ESP32-S3-DevKitC1-N32R8V by Expressif

The project only supports the ESP32-S3 model due to the features I am using. GPIO bundling is only available to S2/S3 models which is essential for keypad input. I am also using the dual core capabilities only available on the S3 model to maximize the performance.

# Project Goal(s)

- :white_check_mark: Create a USB Keypad which allows for single or multiple keystroke inputs at the press of a single button.
    - For example: At the press of a single button, the device could emulate they keyboard input "Hello World!".
- :white_check_mark: Responsive Keypad. No missed input and minimal input-delay.
- :white_square_button: Robust and easy to use firmware.
    - Testing is essential to ensure reliability.
- :white_check_mark: Easy configurability through simple web or desktop application to read and write Configuration data onto the board's flash.
    - It wouldn't make sense to reflash the entire device every single time you want to change macros
- :white_square_button: Integrate Bluetooth stack as an alternative to USB for HID and configuration.
- :white_square_button: Easy reprogrammability through Over-The-Air updates to flash new firmware.

# Current Features
**The device is currently a fully functioning USB Macro Keypad:** All you need to do is flash the firmware using Espressif's IDF, Run the python tool, and setup the macros you want to use!

*Details:*
1) Task-based interface for NVS storage (Read / Write).
2) Interrupt driven keypad matrix control and output generation.
3) Task-based interface for keypad matrix (Start / Stop).
4) python application to customize and flash custom macros to board.
5) USB HID based keypad with CDC for updating macros remotely.

# Next Steps

1) update requirements.txt
2) Test and validate USB HID and CDC functionality.
3) Enforce Mutual exclusion on shared resources effectively.
4) Implement loading config from board into app.
5) Investigate delay between config flash and config update being reflected on device.
6) investigate RAM and task heap/stack usage to optimize memory for smaller ESP32S3 boards.
7) Integrate Bluetooth Stack.
8) Implement OTA Updates.
