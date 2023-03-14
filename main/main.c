#include <stdio.h>

#include "keyboard_wrapper.h"

// Globals for keyboard config
#define num_rows 4
#define num_cols 4
#define debounce_time 50
#define q_size 15
static const int rows [num_rows] = {4,5,6,7};
static const int cols [num_cols] = {15,16,17,18};


void receive_input(keyboard_task_handle_t * handle ){
    //Wait for handle to be initialized
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

    while(1){
        uint32_t result;
        receive_from_queue(handle->kbd_handle, &result);
        printf("row: %lu col: %lu\n", GET_KEY_CODE_ROW(result), GET_KEY_CODE_COL(result));
    }

}


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
    //send_command_control(handle,1);
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
    return handle;
}

void cleanup(keyboard_task_handle_t * kbd_handle, command_task_handle_t* nvs_handle){
    kbd_handle->action = UNINSTALL_KEYBOARD;
    //Spin up task on CPU 1 to command to uninstall keyboard
    send_keyboard_control(kbd_handle, 1);
}


void app_main(void){
    
    keyboard_task_handle_t * kbd_handle = configure_keyboard();

    command_task_handle_t * nvs_handle = configure_nvs();
    
    receive_input(kbd_handle);

    cleanup(kbd_handle, nvs_handle);
}

