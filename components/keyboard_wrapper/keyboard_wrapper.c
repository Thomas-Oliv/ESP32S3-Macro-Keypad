
#include "keyboard_wrapper.h"
#include "freertos/queue.h"
#include <stdio.h>

esp_err_t send_input_event_handler(matrix_kbd_handle_t mkbd_handle, matrix_kbd_event_id_t event, void *event_data, void *handler_args)
{
    uint32_t key_code = (uint32_t)event_data;
    switch (event) {
    case MATRIX_KBD_EVENT_DOWN:
        break;
    case MATRIX_KBD_EVENT_UP:
        send_to_queue(mkbd_handle, &key_code );
        break;
    }
    return ESP_OK;
}

esp_err_t init_keyboard(matrix_kbd_config_t *config, matrix_kbd_handle_t * handle){

    matrix_kbd_handle_t temp_handle;
    esp_err_t err = matrix_kbd_install(config, &temp_handle);
    if(err != ESP_OK) return err;

    err= matrix_kbd_register_event_handler(temp_handle, send_input_event_handler, NULL);
    if(err != ESP_OK) return err;

    err = matrix_kbd_start(temp_handle);
    if(err != ESP_OK) return err;

    *handle = temp_handle;
    return ESP_OK;
}


void keyboard_task(void * parameter){
    keyboard_task_handle_t * handle = (keyboard_task_handle_t * ) parameter;
    // Block indefinitely until we can safely obtain mutex;
    xSemaphoreTake(handle->mutex, portMAX_DELAY);
    switch(handle->action){
        case INSTALL_KEYBOARD:
            init_keyboard(&handle->config, &handle->kbd_handle);
            break;
        case START_KEYBOARD:
            matrix_kbd_start(handle->kbd_handle);
            break;
        case STOP_KEYBOARD:
            matrix_kbd_stop(handle->kbd_handle);
            break;
        case UNINSTALL_KEYBOARD:
            matrix_kbd_uninstall(handle->kbd_handle);
            handle->kbd_handle = NULL;
            break;
    }
    // Release mutex
    xSemaphoreGive(handle->mutex);
    vTaskDelete(NULL);
}

TaskHandle_t send_keyboard_control(keyboard_task_handle_t * handle , BaseType_t priority){
    // Create task with given priority
    TaskHandle_t task_handle = NULL;
    xTaskCreatePinnedToCore(keyboard_task, "keyboard_task", CONFIG_BT_BTU_TASK_STACK_SIZE*3/2, handle, priority, &task_handle, APP_CPU_NUM );
    return task_handle;
}


TaskHandle_t consume_input_task(keyboard_task_handle_t * handle , BaseType_t priority){
    TaskHandle_t task_handle = NULL;

    return task_handle;
}