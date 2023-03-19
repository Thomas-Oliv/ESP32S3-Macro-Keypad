# ESP32-S3 Macro Keypad
Supported Targets:  ESP32-S3

Developed on: ESP32-S3-DevKitC1-N32R8V by Expressif

# Project Goal(s)

- Create a USB and Bluetooth Keypad which allows for single or multiple keystroke inputs at the press of a single button.
    - For example: At the press of a single button, the device could simulate they keyboard input "Hello World!".
- Responsive Keypad. No missed input and minimal input-delay.
- Robust and easy to follow firmware.
- Easy configurability through simple web or desktop application to read and write Configuration data onto the board's flash.
    - It wouldn't make sense to reflash the entire device every single time you want to change macros.
- Easy reprogrammability through Over-The-Air updates to flash new firmware.

# Current Features
1) Task-based interface for NVS storage.
2) Interrupt driven keypad matrix control and output generation.
3) Task-based interface for keypad matrix.
4) python application to customize and flash custom macros to board
5) finished USB HID based keypad output

Todo:
*update requirements.txt*
1) Test and validate USB HID and CDC functionality
2) Enforce Mutual exclusion on shared resources effectively
3) Implement loading config from board into app
4) Investigate delay between config flash and config update being reflected on device.

2) Setup Bluetooth Stack.
3) Implement OTA Updates.
