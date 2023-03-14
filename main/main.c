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
    send_command_control(handle,1);
    /* TODO: Need to make NVS PERSIST BETWEEN FLASHES
     while(1)
    {
        xSemaphoreTake(handle->mutex, portMAX_DELAY);
        //keyboard handle has been initialized
        if(handle->cmds != NULL){
            xSemaphoreGive(handle->mutex);
            break;
        }
        else {        
            xSemaphoreGive(handle->mutex);
            printf("waiting\n");
            vTaskDelay(100);
        }
    }*/
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

    //Spin up task on CPU 1 to command to install keyboard
    send_keyboard_control(handle, 1);
    while(1)
    {
        xSemaphoreTake(handle->mutex, portMAX_DELAY);
        //keyboard handle has been initialized
        if(handle->kbd_handle != NULL){
            xSemaphoreGive(handle->mutex);
            break;
        }
        else {        
            xSemaphoreGive(handle->mutex);
            vTaskDelay(100);
        }
    }
    return handle;
}

void cleanup(hid_handle_t* handle){


    handle->keyboard_handle->action = UNINSTALL_KEYBOARD;
    //Spin up task on CPU 1 to command to uninstall keyboard
    send_keyboard_control(handle->keyboard_handle, 1);
}


void app_main(void){

    keyboard_task_handle_t * kbd_handle = configure_keyboard();
    printf("Configured keyboard.\n");
    command_task_handle_t * nvs_handle = configure_nvs();
    printf("Configured nvs.\n");
    hid_handle_t * hid_handle = malloc(sizeof(hid_handle_t));
    hid_handle->command_handle = nvs_handle;
    hid_handle->keyboard_handle = kbd_handle;

    start_usb_hid_task(hid_handle, 1);
    printf("Started usb hid.\n");
    //cleanup(kbd_handle, nvs_handle);
}

