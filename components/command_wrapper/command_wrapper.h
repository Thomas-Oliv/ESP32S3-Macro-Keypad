
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "command.h"
#include <stdint.h>

typedef enum {
    SAVE_BLOCK,
    GET_BLOCK,
    CLEANUP
} Command_Control_Code_t;

typedef struct command_task_handle_t{
    CMD_BLOCK * cmds;
    Command_Control_Code_t action;
    SemaphoreHandle_t mutex;
} command_task_handle_t;


TaskHandle_t send_command_control(command_task_handle_t * handle , BaseType_t priority);


