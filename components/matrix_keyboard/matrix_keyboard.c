#include "matrix_keyboard.h"

#include <stdio.h>
#include <stdlib.h>
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "driver/dedic_gpio.h"
#include "driver/gpio.h"
#include "driver/gptimer.h"
#include <string.h>
#include "esp_log.h"


#define MAKE_KEY_CODE(row, col) ((row << 8) | (col))
#define GET_KEY_CODE_ROW(code)  ((code >> 8) & 0xFF)
#define GET_KEY_CODE_COL(code)  (code & 0xFF)

typedef struct matrix_kbd_t matrix_kbd_t;
typedef struct isr_arg_t isr_arg_t;
static void IRAM_ATTR gpio_callback(void *args);
static void IRAM_ATTR timer_callback(gptimer_handle_t timer, const gptimer_alarm_event_data_t *edata, void * user_data);

struct matrix_kbd_t {
    dedic_gpio_bundle_handle_t row_bundle;
    dedic_gpio_bundle_handle_t col_bundle;
    matrix_kbd_config_t config;
    gptimer_handle_t debounce_timer;
    QueueHandle_t queue;
    matrix_kbd_event_handler event_handler;
    void *event_handler_args;
    isr_arg_t * isr_args;
    uint32_t row_state [];
} ;


struct isr_arg_t {
    uint32_t row_index;
    matrix_kbd_t * mkbd;
};

esp_err_t install_isr(matrix_kbd_t * mkbd){
    if(mkbd == NULL){
        printf("install_isr: matrix_kbd_t cannot be null\n");
        return ESP_ERR_INVALID_ARG;
    }
    //alloc args for isrs
    mkbd->isr_args = malloc(sizeof(isr_arg_t)*mkbd->config.nr_row_gpios);
    if(mkbd->isr_args == NULL){
        printf("install_isr: %zu\n", ESP_ERR_NO_MEM);
        return ESP_ERR_NO_MEM;
    }
    for(uint32_t i = 0; i < mkbd->config.nr_row_gpios; i++){
        //create arg
        mkbd->isr_args[i].row_index = i;
        mkbd->isr_args[i].mkbd = mkbd;
        // hook isr handler with arg
        gpio_isr_handler_add(mkbd->config.row_gpios[i], gpio_callback, &mkbd->isr_args[i]);
    }
    return ESP_OK;
}

void uninstall_isr(matrix_kbd_t * mkbd){
    if(mkbd == NULL || mkbd->isr_args == NULL){
        return;
    }
    for(uint32_t i = 0; i < mkbd->config.nr_row_gpios; i++){
        // unhook isr
        gpio_isr_handler_remove(mkbd->config.row_gpios[i]);
    }
    //free args
    free(mkbd->isr_args);
    mkbd->isr_args=NULL;
}

void enable_isr(matrix_kbd_config_t config){
    for(uint32_t i = 0; i < config.nr_row_gpios; i++){
        gpio_intr_enable(config.row_gpios[i]);
    }

}

void disable_isr(matrix_kbd_config_t config){
    for(uint32_t i = 0; i < config.nr_row_gpios; i++){
        gpio_intr_disable(config.row_gpios[i]);
    }

}

static void gpio_callback(void *args)
{
    // ESP_DRAM_LOGE ("kbd", "GPIO Callback Core # %lu\n",  (uint32_t)xPortGetCoreID());
    isr_arg_t *arg = (isr_arg_t *)args;
    // temporarily disable interrupt
    disable_isr(arg->mkbd->config);
    // set specific row to low
    dedic_gpio_bundle_write(arg->mkbd->row_bundle, 1 << arg->row_index, 0);
    //set columns to high
    dedic_gpio_bundle_write(arg->mkbd->col_bundle, (1 << arg->mkbd->config.nr_col_gpios) - 1, (1 << arg->mkbd->config.nr_col_gpios) - 1);
    //start debounce timer
    gptimer_set_raw_count(arg->mkbd->debounce_timer, 0);
    gptimer_start(arg->mkbd->debounce_timer);
}

static void timer_callback(gptimer_handle_t timer, const gptimer_alarm_event_data_t *edata, void * user_data)
{
    // ESP_DRAM_LOGE ("kbd", "Timer callback Core # %lu\n",  (uint32_t)xPortGetCoreID());
    matrix_kbd_t * mkbd = (matrix_kbd_t *)user_data;
    // stop timer immediately
    gptimer_stop(mkbd->debounce_timer);

    // Get IO
    uint32_t row_out = dedic_gpio_bundle_read_out(mkbd->row_bundle);
    uint32_t col_in = dedic_gpio_bundle_read_in(mkbd->col_bundle);
    
    //Get what key was pressed
    row_out = (~row_out) & ((1 << mkbd->config.nr_row_gpios) - 1);
    int row = -1;
    int col = -1;
    uint32_t key_code = 0;

    while (row_out) {
        row = __builtin_ffs(row_out) - 1;
        uint32_t changed_col_bits = mkbd->row_state[row] ^ col_in;
        while (changed_col_bits) {
            col = __builtin_ffs(changed_col_bits) - 1;
            key_code = MAKE_KEY_CODE(row, col);
            if (col_in & (1 << col)) {
                // Key Up Event
                mkbd->event_handler(mkbd, MATRIX_KBD_EVENT_UP, (void *)key_code, mkbd->event_handler_args);
            } else {
                // Key Down Event
                mkbd->event_handler(mkbd, MATRIX_KBD_EVENT_DOWN, (void *)key_code, mkbd->event_handler_args) ;
            }
            changed_col_bits = changed_col_bits & (changed_col_bits - 1);
        }
        mkbd->row_state[row] = col_in;
        row_out = row_out & (row_out - 1);
    }

    // row lines set to high level
    dedic_gpio_bundle_write(mkbd->row_bundle, (1 << mkbd->config.nr_row_gpios) - 1, (1 << mkbd->config.nr_row_gpios) - 1);
    // col lines set to low level
    dedic_gpio_bundle_write(mkbd->col_bundle, (1 << mkbd->config.nr_col_gpios) - 1, 0);
    // Wait for next input
    enable_isr(mkbd->config);
}

esp_err_t validate_config(const matrix_kbd_config_t *config){
    esp_err_t err = ESP_ERR_INVALID_ARG;
    if(config->col_gpios == NULL){
        printf("validate_config: col_gpios cannot be null\n");
    } else if(config->row_gpios == NULL){
        printf("validate_config: row_gpios cannot be null\n");
    } else if(config->nr_col_gpios == 0){
        printf("validate_config: nr_col_gpios cannot be 0\n");
    } else if(config->nr_row_gpios == 0){
        printf("validate_config: nr_row_gpios cannot be 0\n");
    } else if(config->debounce_ms == 0){
        printf("validate_config: debounce_ms cannot be 0\n");
    } else if(config->queue_size == 0){
        printf("validate_config: queue_size cannot be 0\n");
    } else{
        err = ESP_OK;
    }
    return err;
}

esp_err_t setup_gpio(const matrix_kbd_config_t *config, matrix_kbd_t* mkbd) {
   
    //enable interrupts on each gpio row pin
    gpio_config_t io_conf = {
        .intr_type = GPIO_INTR_ANYEDGE,
        .mode = GPIO_MODE_INPUT_OUTPUT_OD,
        .pull_up_en = 1
    };
    //setup row gpio
    for (int i = 0; i < config->nr_row_gpios; i++) {
        io_conf.pin_bit_mask = 1ULL << config->row_gpios[i];
        gpio_config(&io_conf);
    }
    //create row bundles
    dedic_gpio_bundle_config_t bundle_row_config = {
        .gpio_array = config->row_gpios,
        .array_size = config->nr_row_gpios,
        .flags = {
            .in_en = 1,
            .out_en = 1,
        },
    };
    esp_err_t err = dedic_gpio_new_bundle(&bundle_row_config, &mkbd->row_bundle);
    if(err != ESP_OK){
        //TODO: Change print here
        printf("setup_gpio: Failed to create row bundles: %zu\n", err);
        return err;
    }

    //Ensure interrupts are disabled for columns
    io_conf.intr_type = GPIO_INTR_DISABLE;
    for (int i = 0; i < config->nr_col_gpios; i++) {
        io_conf.pin_bit_mask = 1ULL << config->col_gpios[i];
        gpio_config(&io_conf);
    }

    dedic_gpio_bundle_config_t bundle_col_config = {
        .gpio_array = config->col_gpios,
        .array_size = config->nr_col_gpios,
        .flags = {
            .in_en = 1,
            .out_en = 1,
        },
    };

    err = dedic_gpio_new_bundle(&bundle_col_config, &mkbd->col_bundle);
    if(err != ESP_OK){
        //TODO: Change print here
        printf("setup_gpio: Failed to create column bundles: %zu\n", err);
        return err;
    }

    return ESP_OK;
}


esp_err_t setup_timer(void* callback, matrix_kbd_t* mkbd){

    if (callback == NULL || mkbd == NULL || mkbd->config.queue_size == 0 || mkbd->config.debounce_ms ==0 ) {
        printf("setup_timer: %zu\n", ESP_ERR_INVALID_ARG);
        return ESP_ERR_INVALID_ARG;
    }

    mkbd->queue = xQueueCreate(mkbd->config.queue_size, sizeof(uint32_t));
    if(mkbd->queue  == 0){
        printf("setup_timer: Could not create queue: %zu\n", ESP_ERR_NO_MEM);
        return ESP_ERR_NO_MEM;
    }

    gptimer_config_t timer_config = {
        .clk_src = GPTIMER_CLK_SRC_DEFAULT,
        .direction = GPTIMER_COUNT_UP,
        .resolution_hz = 1000000, // 1MHz, 1 tick=1us
    };
    esp_err_t err= gptimer_new_timer(&timer_config, &mkbd->debounce_timer);
    if(err != ESP_OK){
        //TODO: Edit this print to be better
        printf("setup_timer: Failed to create timer: %zu", err);
        return err;
    }

    gptimer_alarm_config_t alarm_config = {
        .alarm_count = mkbd->config.debounce_ms*1000, // period = 1s
    };
    err= gptimer_set_alarm_action(mkbd->debounce_timer, &alarm_config);
    if(err != ESP_OK){
        //TODO: Edit this print to be better
        printf("setup_timer: Failed to set alarm config: %zu", err);
        return err;
    }


    gptimer_event_callbacks_t cbs = {
        .on_alarm = callback,
    };
    err= gptimer_register_event_callbacks(mkbd->debounce_timer, &cbs, mkbd); 
    if(err != ESP_OK){
        //TODO: Edit this print to be better
        printf("setup_timer: Failed to register timer event callback: %zu", err);
        return err;
    }

    return ESP_OK;
}   

esp_err_t matrix_kbd_install(const matrix_kbd_config_t *config, matrix_kbd_handle_t *mkbd_handle)
{
    if(mkbd_handle == NULL){
        printf("matrix_kbd_install: Handle cannot be null: %zu\n", ESP_ERR_INVALID_ARG);
        return ESP_ERR_INVALID_ARG;
    }
    //ensure input is valid
    esp_err_t err = validate_config(config);
    if(err != ESP_OK) return err;

    matrix_kbd_t *mkbd = calloc(1, sizeof(matrix_kbd_t) + (config->nr_row_gpios) * sizeof(uint32_t));
    if(mkbd == NULL){
        printf("matrix_kbd_install: Failed to calloc.\n");
        return ESP_ERR_NO_MEM;
    }
    //Copy config
    memcpy(&mkbd->config,config,sizeof(matrix_kbd_config_t));

    //init isr
    gpio_install_isr_service(0);
    
    //setup gpio
    err = setup_gpio(config, mkbd);
    if( err != ESP_OK) return err;

    //setup interrupts
    err = install_isr(mkbd);
    if( err != ESP_OK) return err;
    //disable interrupts
    disable_isr(mkbd->config);

    // Create a ont-shot os timer, used for key debounce
    err = setup_timer(timer_callback, mkbd);
    if( err != ESP_OK) return err;

    *mkbd_handle = mkbd;
    return ESP_OK;

}


esp_err_t matrix_kbd_uninstall(matrix_kbd_handle_t mkbd_handle)
{
    //cleanup timer
    gptimer_stop(mkbd_handle->debounce_timer);
    gptimer_disable(mkbd_handle->debounce_timer);
    gptimer_del_timer(mkbd_handle->debounce_timer);
    //free gpio interrupt parameters
    uninstall_isr(mkbd_handle);
    //delete bundles
    dedic_gpio_del_bundle(mkbd_handle->col_bundle);
    dedic_gpio_del_bundle(mkbd_handle->row_bundle);

    vQueueDelete(mkbd_handle->queue);
    //Free memory
    free(mkbd_handle);
    return ESP_OK;
}

esp_err_t matrix_kbd_start(matrix_kbd_handle_t mkbd_handle)
{

    gptimer_enable(mkbd_handle->debounce_timer);
    // row lines set to high level
    dedic_gpio_bundle_write(mkbd_handle->row_bundle, (1 << mkbd_handle->config.nr_row_gpios) - 1, (1 << mkbd_handle->config.nr_row_gpios) - 1);
    // col lines set to low level
    dedic_gpio_bundle_write(mkbd_handle->col_bundle, (1 << mkbd_handle->config.nr_col_gpios) - 1, 0);

    for (int i = 0; i < mkbd_handle->config.nr_row_gpios; i++) {
        mkbd_handle->row_state[i] = (1 << mkbd_handle->config.nr_col_gpios) - 1;
    }

    // only enable row line interrupt
    enable_isr(mkbd_handle->config);

    return ESP_OK;

}

esp_err_t matrix_kbd_stop(matrix_kbd_handle_t mkbd_handle)
{

    //Stop timer
    gptimer_stop(mkbd_handle->debounce_timer);
    gptimer_disable(mkbd_handle->debounce_timer);

    // Disable interrupt
    disable_isr(mkbd_handle->config);

    return ESP_OK;
}


esp_err_t matrix_kbd_register_event_handler(matrix_kbd_handle_t mkbd_handle, matrix_kbd_event_handler handler, void *args)
{   
    if(mkbd_handle == NULL){
        printf("matrix_kbd_register_event_handler: %zu\n", ESP_ERR_INVALID_ARG);
        return ESP_ERR_INVALID_ARG;
    }
    mkbd_handle->event_handler = handler;
    mkbd_handle->event_handler_args = args;
    return ESP_OK;
}

void send_to_queue(matrix_kbd_handle_t mkbd_handle, void * arg){
    if(mkbd_handle == NULL || arg == NULL || mkbd_handle->queue == NULL) return;
    xQueueSendFromISR(mkbd_handle->queue, arg, NULL);
}

void receive_from_queue(matrix_kbd_handle_t mkbd_handle, void * arg){
    if(mkbd_handle == NULL || arg == NULL || mkbd_handle->queue == NULL) return;
    xQueueReceive(mkbd_handle->queue, arg, portMAX_DELAY);
}

uint32_t get_indx(matrix_kbd_handle_t handle, uint32_t key_code){
    if(handle == NULL) return UINT32_MAX;
    //Offset row
    uint32_t result = handle->config.nr_col_gpios*GET_KEY_CODE_ROW(key_code);
    // add column;
    return result + GET_KEY_CODE_COL(key_code);
}