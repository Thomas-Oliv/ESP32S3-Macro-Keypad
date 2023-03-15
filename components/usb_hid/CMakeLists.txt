idf_component_register(SRCS "hid_copy.c" "usb_hid.c"
                    INCLUDE_DIRS "."
                    REQUIRES "keyboard_wrapper"
                    PRIV_REQUIRES driver
                    )

