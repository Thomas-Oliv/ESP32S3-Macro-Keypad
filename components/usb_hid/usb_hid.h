
#include "keyboard_wrapper.h"

typedef struct hid_handle_t{
    command_task_handle_t * command_handle;
    keyboard_task_handle_t * keyboard_handle;
} hid_handle_t;


TaskHandle_t start_usb_hid_task(hid_handle_t * handle , BaseType_t priority);
