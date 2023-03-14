
#include "matrix_keyboard.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "command_wrapper.h"
#include <stdint.h>

typedef enum {
    INSTALL_KEYBOARD,
    START_KEYBOARD,
    STOP_KEYBOARD,
    UNINSTALL_KEYBOARD
} Keyboard_Control_Code_t;

typedef struct keyboard_task_handle_t{
    matrix_kbd_config_t config;
    matrix_kbd_handle_t kbd_handle;
    Keyboard_Control_Code_t action;
    SemaphoreHandle_t mutex;
} keyboard_task_handle_t;


TaskHandle_t send_keyboard_control(keyboard_task_handle_t * handle , BaseType_t priority);



