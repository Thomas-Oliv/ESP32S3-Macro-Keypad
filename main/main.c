#include <stdio.h>

#include "usb_hid.h"
// Globals for keyboard config
#define num_rows 4
#define num_cols 4
#define debounce_time 50
#define q_size 15
static const int rows [num_rows] = {4,5,6,7};
static const int cols [num_cols] = {15,16,17,18};

command_task_handle_t*  configure_nvs(){
    if(init_storage() != ESP_OK)
    {
        printf( "Failed to init nvs\n");
        return NULL;
    } 
    command_task_handle_t * handle = malloc(sizeof(command_task_handle_t));
    handle->cmds = NULL;
    handle->action = GET_BLOCK;
    handle->mutex = xSemaphoreCreateMutex();
    if(handle->mutex ==NULL){
        printf("configure_nvs: failed to malloc cmd\n");
        return NULL;
    }
    send_command_control(handle, 1);
    return handle;
}

keyboard_task_handle_t * configure_keyboard()
{

    // Setup keyboard matrix configuration
    matrix_kbd_config_t config = {
        .nr_row_gpios = num_rows,
        .nr_col_gpios = num_cols,
        //TODO: These *should* be globally accessible across processes. Need to verify
        .col_gpios = cols,
        .row_gpios = rows,
        .queue_size = q_size,
        .debounce_ms = debounce_time,
    };

    // create task param, specify action, copy config and pointer to handle
    keyboard_task_handle_t * handle = malloc(sizeof(keyboard_task_handle_t));
    handle->kbd_handle=  NULL;
    handle->config = config;
    handle->action= INSTALL_KEYBOARD;
    handle->mutex = xSemaphoreCreateMutex();
    if( handle->mutex == NULL ){
        printf("app_main: failed to create mutex\n");
        return NULL;
    }   
    send_keyboard_control(handle,1);
    return handle;
}

void app_main(void){

    keyboard_task_handle_t * kbd_handle = configure_keyboard();
    printf("Configured keyboard.\n");
    command_task_handle_t * nvs_handle = configure_nvs();
    printf("Configured nvs.\n");
    hid_handle_t * hid_handle = malloc(sizeof(hid_handle_t));
    if(kbd_handle == NULL || nvs_handle == NULL || hid_handle == NULL )
    {
        printf("app_main: failed to malloc\n");
        abort();
    }

    hid_handle->command_handle = nvs_handle;
    hid_handle->keyboard_handle = kbd_handle;
    // Start Receiving input
    start_usb_task(hid_handle, 3);
    printf("Configured Usb.\n");
}
