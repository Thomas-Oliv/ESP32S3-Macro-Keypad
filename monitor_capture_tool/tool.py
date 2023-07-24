import serial

device_port = input("Device COM Port:")

with serial.Serial(port= device_port,baudrate=115200) as s:
    print("Found Device")
    while(1):
        line = s.readline().decode('utf-8')
        if line != '\n':
            print(line.strip())
        if "~~Start~~" in line:
            break
    print("STARTING CAPTURE")
    with open("output.csv", "w+") as f:
        while(1):
            line = s.readline().decode('utf-8')
            if "~~End~~" in line:
                break
            elif line != '\n':
                f.write(line.strip()+"\n")
print("DONE")
