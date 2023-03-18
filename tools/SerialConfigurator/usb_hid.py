from enum import Enum
from struct import pack, unpack_from

L_SHIFT = 0x02
R_SHIFT = 0x20
#key code used to represent a delay type
delay_code = 0x01
#number of bytes required to pack a single key stroke command
key_stroke_size = 0x04

class KeyStroke():
    def __init__(self, modifier, code, delay_time=0):
        self.modifier:int = modifier # use for keycode modifier or delay units
        self.key_code:int = code    #keycode or delay id
        self.delay:int = delay_time #delay amount


class Device():
    hwid: str
    rows: int
    cols: int
    data: list[list[KeyStroke]]

    def __init__(self, hwid, rows, cols):
        self.hwid = hwid
        self.rows=rows
        self.cols=cols
        self.data= [[]]*self.rows*self.cols


def get_key_dropdown_values(modifier ):
    data = []
    is_shifted = modifier & modifiers[2][1]  or modifier & modifiers[6][1]
    for name, value in common_keys:
        data.append((name,value))
    
    for name_lower, name_upper, value in shifted_keys:
        if(is_shifted):
            data.append((name_upper, value))
        else:
            data.append((name_lower, value))
    return data  

# VERIFIED
def serialize_data(data: list[list[KeyStroke]]):
    packed_result =b''
    total_size =0
    for command in data:
        size = 0
        packed_keycode = b''
        for keystroke in command:
            #pack keystrokes and keep track of number of keystrokes stored
            packed_keycode += pack("<BBH",keystroke.modifier,keystroke.key_code,keystroke.delay)
            size += 1
        #keep track of number of bytes used
        total_size += size*key_stroke_size + 2
        #write number of keystrokes to beginning of packed block
        packed_result += pack("<H", size) + packed_keycode
    #return packed object and total size in bytes
    return packed_result, total_size

#Should be good
def deserialize_data( packed_obj, total_size):
    final_result = []
    indx =0
    state = DeserializeState.START_BLOCK
    while(indx < total_size):
        match state:
            case DeserializeState.START_BLOCK:
                #Get length of command block
                command = []
                cmd_len = unpack_from("<H",packed_obj, indx)
                offset = 0
                indx += 1
                state = DeserializeState.KEYSTROKE
            case DeserializeState.KEYSTROKE:
                #Keep unpacking each command one keystroke at a time
                if(offset < cmd_len):
                    #Get keystroke
                    modifier, key, delay = unpack_from("<BBH",packed_obj,indx+offset*key_stroke_size)
                    offset += 1
                    command.append(KeyStroke(modifier,key,delay))
                else:
                    #add completed command and reset
                    final_result.append(command)
                    indx += offset*key_stroke_size
                    state= DeserializeState.START_BLOCK
    return final_result

#Two states used for deserialization
class DeserializeState(Enum):
    START_BLOCK = 0
    KEYSTROKE = 1


delay_units = [
    ("Milliseconds", 0x00),
    ("Seconds", 0x01)
]

#keycode modifiers (readable name & bit)
modifiers = [ 
    ("NONE", 0x00), 
    ("Left Control" , 0x01), 
    ("Left Shift" , L_SHIFT),
    ("Left Alt" , 0x04),
    ("Left Meta" ,0x08),
    ("Right Control" , 0x10),
    ("Right Shift" , R_SHIFT),
    ("Right Alt" , 0x40),
    ("Right Meta" , 0x80)
]

#Supported keycodes common to both shift/unshift (readable name & keycode)
common_keys =[
    ("None",0x00),
    #("Error Roll Over", 0x01) -- This should not occur with implementation -- Reusing key to represent a delay
    ("Enter",0x28),
    ("Escape", 0x29),
    ("Backspace",0x2a),
    ("Tab",0x2b),
    ("Space",0x2c),
    #("CapsLock",0x39),
    ("F1",0x3a),
    ("F2",0x3b),
    ("F3",0x3c),
    ("F4",0x3d),
    ("F5",0x3e),
    ("F6",0x3f),
    ("F7",0x40),
    ("F8",0x41),
    ("F9",0x42),
    ("F10",0x43),
    ("F12",0x44),
    ("F12",0x45),
    ("Print Screen",0x46),
    #("Scroll Lock", 0x47),
    ("Pause",0x48),
    ("Insert",0x49),
    ("Home",0x4a),
    ("Page Up",0x4b),
    ("Delete",0x4c),
    ("End",0x4d),
    ("Page Down",0x4e),
    ("Right",0x4f),
    ("Left",0x50),
    ("Down",0x51),
    ("Up",0x52),
    #("Compose",0x65),
    #("Power",0x66),
    #("Open",0x74),
    #("Help",0x75),
    #("Menu",0x76),
    #("Select",0x77),
    #("Stop",0x78),
    ("Redo",0x79),
    ("Undo",0x7a),
    ("Cut",0x7b),
    ("Copy",0x7c),
    ("Paste",0x7d),
    ("Find",0x7e),
    ("Mute",0x7f),
    ("Volume Up",0x80),
    ("Volume Down",0x81),
    ("Media Play/Pause",0xe8),
    #("Media Stop",0xe9),
    #("Media Previous",0xea),
    #("Media Next",0xeb),
    #("Media Eject",0xec),
    #("Media Volume Up",0xed),
    #("Media Volume Down",0xee),
    #("Media Mute",0xef),
    #("WWW",0xf0),
    #("Media Back",0xf1),
    #("Media Forward",0xf2),
    #("Media Stop",0xf3),
    #("Media Find",0xf4),
    #("Media Scroll Up",0xf5),
    #("Media Scroll Down",0xf6),
    #("Media Edit",0xf7),
    #("Media Sleep",0xf8),
    #("Media Coffee",0xf9),
    #("Media Refresh",0xfa),
    ("Media Calc",0xfb)
]

#Supported keycodes which show shifted variant (readable name & keycode)
shifted_keys  = [
    ("a","A", 0x40),
    ("b","B", 0x05),
    ("c","C", 0x06),
    ("d","D", 0x07),
    ("e","E", 0x08),
    ("f","F", 0x09),
    ("g","G", 0x0a),
    ("h","H", 0x0b),
    ("i","I", 0x0c),
    ("j","J", 0x0d),
    ("k","K", 0x0e),
    ("l","L", 0x0f),
    ("m","M", 0x10),
    ("n","N", 0x11),
    ("o","O", 0x12),
    ("p","P", 0x13),
    ("q","Q", 0x14),
    ("r","R", 0x15),
    ("s","S", 0x16),
    ("t","T", 0x17),
    ("u","U", 0x18),
    ("v","V", 0x19),
    ("w","W", 0x1a),
    ("x","X", 0x1b),
    ("y","Y", 0x1c),
    ("z","Z", 0x1d),
    ("1","!", 0x2e),
    ("2","@", 0x1f),
    ("34","#", 0x20),
    ("4","$", 0x21),
    ("5","%", 0x22),
    ("6","^", 0x23),
    ("7","&", 0x24),
    ("8","*", 0x25),
    ("9","(", 0x26),
    ("0",")", 0x27),
    ("-","_", 0x2d),
    ("=","+", 0x2e),
    ("[","{", 0x2f),
    ("]","}", 0x30),
    ("\\","|", 0x31),
    (";",":", 0x33),
    ("'","\"", 0x34),
    ("`","~", 0x35),
    (",","<", 0x36),
    (".",">", 0x37),
    ("/","?", 0x38),
]


#~~~~~~~~~~~~~~~~~ NOT IMPLEMENTED ~~~~~~~~~~~~~~~~~#

#KEY_HASHTILDE 0x32 # Keyboard Non-US # and ~

#KEY_NUMLOCK 0x53 # Keyboard Num Lock and Clear
#KEY_KPSLASH 0x54 # Keypad /
#KEY_KPASTERISK 0x55 # Keypad *
#KEY_KPMINUS 0x56 # Keypad -
#KEY_KPPLUS 0x57 # Keypad +
#KEY_KPENTER 0x58 # Keypad ENTER
#KEY_KP1 0x59 # Keypad 1 and End
#KEY_KP2 0x5a # Keypad 2 and Down Arrow
#KEY_KP3 0x5b # Keypad 3 and PageDn
#KEY_KP4 0x5c # Keypad 4 and Left Arrow
#KEY_KP5 0x5d # Keypad 5
#KEY_KP6 0x5e # Keypad 6 and Right Arrow
#KEY_KP7 0x5f # Keypad 7 and Home
#KEY_KP8 0x60 # Keypad 8 and Up Arrow
#KEY_KP9 0x61 # Keypad 9 and Page Up
#KEY_KP0 0x62 # Keypad 0 and Insert
#KEY_KPDOT 0x63 # Keypad . and Delete

#KEY_102ND 0x64 # Keyboard Non-US \ and |
#KEY_KPEQUAL 0x67 # Keypad =


# 0x82  Keyboard Locking Caps Lock
# 0x83  Keyboard Locking Num Lock
# 0x84  Keyboard Locking Scroll Lock
#KEY_KPCOMMA 0x85 # Keypad Comma
# 0x86  Keypad Equal Sign
#KEY_RO 0x87 # Keyboard International1
#KEY_KATAKANAHIRAGANA 0x88 # Keyboard International2
#KEY_YEN 0x89 # Keyboard International3
#KEY_HENKAN 0x8a # Keyboard International4
#KEY_MUHENKAN 0x8b # Keyboard International5
#KEY_KPJPCOMMA 0x8c # Keyboard International6
# 0x8d  Keyboard International7
# 0x8e  Keyboard International8
# 0x8f  Keyboard International9
#KEY_HANGEUL 0x90 # Keyboard LANG1
#KEY_HANJA 0x91 # Keyboard LANG2
#KEY_KATAKANA 0x92 # Keyboard LANG3
#KEY_HIRAGANA 0x93 # Keyboard LANG4
#KEY_ZENKAKUHANKAKU 0x94 # Keyboard LANG5
# 0x95  Keyboard LANG6
# 0x96  Keyboard LANG7
# 0x97  Keyboard LANG8
# 0x98  Keyboard LANG9
# 0x99  Keyboard Alternate Erase
# 0x9a  Keyboard SysReq/Attention
# 0x9b  Keyboard Cancel
# 0x9c  Keyboard Clear
# 0x9d  Keyboard Prior
# 0x9e  Keyboard Return
# 0x9f  Keyboard Separator
# 0xa0  Keyboard Out
# 0xa1  Keyboard Oper
# 0xa2  Keyboard Clear/Again
# 0xa3  Keyboard CrSel/Props
# 0xa4  Keyboard ExSel

# 0xb0  Keypad 00
# 0xb1  Keypad 000
# 0xb2  Thousands Separator
# 0xb3  Decimal Separator
# 0xb4  Currency Unit
# 0xb5  Currency Sub-unit
# 0xb6  Keypad (
# 0xb7  Keypad )
# 0xb8  Keypad {
# 0xb9  Keypad }
# 0xba  Keypad Tab
# 0xbb  Keypad Backspace
# 0xbc  Keypad A
# 0xbd  Keypad B
# 0xbe  Keypad C
# 0xbf  Keypad D
# 0xc0  Keypad E
# 0xc1  Keypad F
# 0xc2  Keypad XOR
# 0xc3  Keypad ^
# 0xc4  Keypad %
# 0xc5  Keypad <
# 0xc6  Keypad >
# 0xc7  Keypad &
# 0xc8  Keypad &&
# 0xc9  Keypad |
# 0xca  Keypad ||
# 0xcb  Keypad :
# 0xcc  Keypad #
# 0xcd  Keypad Space
# 0xce  Keypad @
# 0xcf  Keypad !
# 0xd0  Keypad Memory Store
# 0xd1  Keypad Memory Recall
# 0xd2  Keypad Memory Clear
# 0xd3  Keypad Memory Add
# 0xd4  Keypad Memory Subtract
# 0xd5  Keypad Memory Multiply
# 0xd6  Keypad Memory Divide
# 0xd7  Keypad +/-
# 0xd8  Keypad Clear
# 0xd9  Keypad Clear Entry
# 0xda  Keypad Binary
# 0xdb  Keypad Octal
# 0xdc  Keypad Decimal
# 0xdd  Keypad Hexadecimal

#~~~~~~~~~~~~~~~~~ NOT IMPLEMENTED ~~~~~~~~~~~~~~~~~#