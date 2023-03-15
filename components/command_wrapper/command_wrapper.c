
#include "command_wrapper.h"
#include <stdio.h>



void command_task(void * parameter){
    command_task_handle_t * handle = (command_task_handle_t * ) parameter;
    // Block indefinitely until we can safely obtain mutex;
    xSemaphoreTake(handle->mutex, portMAX_DELAY);
    switch(handle->action){
        case SAVE_BLOCK:
            save_cmd_block(handle->cmds );
            break;
        case GET_BLOCK:
            handle->cmds = get_cmd_block();
            break;
        case CLEANUP:
            cleanup_cmd_block(handle->cmds);
            handle->cmds = NULL;
            break;
    }
    // Release mutex
    xSemaphoreGive(handle->mutex);
    vTaskDelete(NULL);
}

TaskHandle_t send_command_control(command_task_handle_t * handle , BaseType_t priority){
    // Create task with given priority
    TaskHandle_t task_handle = NULL;
    xTaskCreatePinnedToCore(command_task, "command_task", CONFIG_BT_BTU_TASK_STACK_SIZE*3/2, handle, priority, &task_handle, APP_CPU_NUM );
    return task_handle;
}
