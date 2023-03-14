# ESP32-S3 Macro Keypad
| Supported Targets  ESP32-S3 |


# Project Goal(s)

- Create a USB or Bluetooth Keypad which allows for single or multiple keystroke inputs at the press of a single button.
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

Todo:
1) Extract command based on key and send data up through USB or Bluetooth stack to generate macro key output.
    1) Setup Bluetooth/USB HID Stack.
    2) Consume keystroke and integrate NVS command data into HID output.
2) Write new commands to NVS over USB or Bluetooth.
    1) Implement Interface on Host.
    2) Implement Service on Device.
3) Implement OTA Updates.
