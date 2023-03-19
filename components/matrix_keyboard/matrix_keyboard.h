
#pragma once

#include <stdint.h>
#include "esp_err.h"

/**
 * @brief Type defined for matrix keyboard handle
 *
 */
typedef struct matrix_kbd_t *matrix_kbd_handle_t;

/**
 * @brief Matrix keyboard event ID
 *
 */
typedef enum {
    MATRIX_KBD_EVENT_DOWN, /*!< Key is pressed down */
    MATRIX_KBD_EVENT_UP    /*!< Key is released */
} matrix_kbd_event_id_t;


typedef esp_err_t (*matrix_kbd_event_handler)(matrix_kbd_handle_t mkbd_handle, matrix_kbd_event_id_t event, void *event_data, void *args);


typedef struct matrix_kbd_config_t {
    uint32_t nr_row_gpios; 
    uint32_t nr_col_gpios; 
    const int * row_gpios; 
    const int * col_gpios;  
    uint32_t debounce_ms; 
    uint32_t queue_size;
} matrix_kbd_config_t;

/**
 * @brief Install matrix keyboard driver
 *
 * @param[in] config Configuration of matrix keyboard driver
 * @param[out] mkbd_handle Returned matrix keyboard handle if installation succeed
 * @return
 *      - ESP_OK: Install matrix keyboard driver successfully
 *      - ESP_ERR_INVALID_ARG: Install matrix keyboard driver failed because of some invalid argument
 *      - ESP_ERR_NO_MEM: Install matrix keyboard driver failed because there's no enough capable memory
 *      - ESP_FAIL: Install matrix keyboard driver failed because of other error
 */
esp_err_t matrix_kbd_install(const matrix_kbd_config_t *config, matrix_kbd_handle_t *mkbd_handle);

/**
 * @brief Uninstall matrix keyboard driver
 *
 * @param[in] mkbd_handle Handle of matrix keyboard that return from `matrix_kbd_install`
 * @return
 *      - ESP_OK: Uninstall matrix keyboard driver successfully
 *      - ESP_ERR_INVALID_ARG: Uninstall matrix keyboard driver failed because of some invalid argument
 *      - ESP_FAIL: Uninstall matrix keyboard driver failed because of other error
 */
esp_err_t matrix_kbd_uninstall(matrix_kbd_handle_t mkbd_handle);

/**
 * @brief Start matrix keyboard driver
 *
 * @param[in] mkbd_handle Handle of matrix keyboard that return from `matrix_kbd_install`
 * @return
 *      - ESP_OK: Start matrix keyboard driver successfully
 *      - ESP_ERR_INVALID_ARG: Start matrix keyboard driver failed because of some invalid argument
 *      - ESP_FAIL: Start matrix keyboard driver failed because of other error
 */
esp_err_t matrix_kbd_start(matrix_kbd_handle_t mkbd_handle);

/**
 * @brief Stop matrix kayboard driver
 *
 * @param[in] mkbd_handle Handle of matrix keyboard that return from `matrix_kbd_install`
 * @return
 *      - ESP_OK: Stop matrix keyboard driver successfully
 *      - ESP_ERR_INVALID_ARG: Stop matrix keyboard driver failed because of some invalid argument
 *      - ESP_FAIL: Stop matrix keyboard driver failed because of other error
 */
esp_err_t matrix_kbd_stop(matrix_kbd_handle_t mkbd_handle);

/**
 * @brief Register matrix keyboard event handler
 *
 * @param[in] mkbd_handle Handle of matrix keyboard that return from `matrix_kbd_install`
 * @param[in] handler Event handler
 * @param[in] args Arguments that will be passed to the handler
 * @return
 *      - ESP_OK: Register event handler successfully
 *      - ESP_ERR_INVALID_ARG: Register event handler failed because of some invalid argument
 *      - ESP_FAIL: Register event handler failed because of other error
 */
esp_err_t matrix_kbd_register_event_handler(matrix_kbd_handle_t mkbd_handle, matrix_kbd_event_handler handler, void *args);


void send_to_queue(matrix_kbd_handle_t mkbd_handle, void * arg);

void receive_from_queue(matrix_kbd_handle_t mkbd_handle, void * arg);

uint32_t get_indx(matrix_kbd_handle_t handle, uint32_t key_code);

uint32_t get_size(matrix_kbd_handle_t handle);