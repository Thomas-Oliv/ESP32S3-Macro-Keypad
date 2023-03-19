idf_component_register(SRCS "usb_base.c" "crc16.c" "usb_hid.c"
                    INCLUDE_DIRS "."
                    REQUIRES "keyboard_wrapper"
                    PRIV_REQUIRES driver
                    )

