/*
 * SPDX-FileCopyrightText: 2022-2023 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: Unlicense OR CC0-1.0
 */
#include "usb_hid.h"
#include <stdlib.h>
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "tinyusb.h"
#include "class/hid/hid_device.h"
#include "driver/gpio.h"

#define APP_BUTTON (GPIO_NUM_0) // Use BOOT signal by default

/************* TinyUSB descriptors ****************/

#define TUSB_DESC_TOTAL_LEN      (TUD_CONFIG_DESC_LEN + CFG_TUD_HID * TUD_HID_DESC_LEN)

const uint8_t hid_report_descriptor[] = {
    TUD_HID_REPORT_DESC_KEYBOARD(HID_REPORT_ID(HID_ITF_PROTOCOL_KEYBOARD) )
};

/**
 * @brief Configuration descriptor
 *
 * This is a simple configuration descriptor that defines 1 configuration and 1 HID interface
 */
static const uint8_t hid_configuration_descriptor[] = {
    // Configuration number, interface count, string index, total length, attribute, power in mA
    TUD_CONFIG_DESCRIPTOR(1, 1, 0, TUSB_DESC_TOTAL_LEN, TUSB_DESC_CONFIG_ATT_REMOTE_WAKEUP, 100),

    // Interface number, string index, boot protocol, report descriptor len, EP In address, size & polling interval
    TUD_HID_DESCRIPTOR(0, 4, false, sizeof(hid_report_descriptor), 0x81, 16, 10),
};

/********* TinyUSB HID callbacks ***************/

// Invoked when received GET HID REPORT DESCRIPTOR request
// Application return pointer to descriptor, whose contents must exist long enough for transfer to complete
uint8_t const *tud_hid_descriptor_report_cb(uint8_t instance)
{
    return &hid_report_descriptor;
}

// Invoked when received GET_REPORT control request
// Application must fill buffer report's content and return its length.
// Return zero will cause the stack to STALL request
uint16_t tud_hid_get_report_cb(uint8_t instance, uint8_t report_id, hid_report_type_t report_type, uint8_t* buffer, uint16_t reqlen)
{
  (void) instance;
  (void) report_id;
  (void) report_type;
  (void) buffer;
  (void) reqlen;
  return 0;
}

// Invoked when received SET_REPORT control request or
// received data on OUT endpoint ( Report ID = 0, Type = 0 )
void tud_hid_set_report_cb(uint8_t instance, uint8_t report_id, hid_report_type_t report_type, uint8_t const* buffer, uint16_t bufsize)
{
}

static void usb_hid_task(void * parameter)
{
    hid_handle_t * handle = (hid_handle_t* )parameter;
    // Initialize button that will trigger HID reports
    const gpio_config_t boot_button_config = {
        .pin_bit_mask = BIT64(APP_BUTTON),
        .mode = GPIO_MODE_INPUT,
        .intr_type = GPIO_INTR_DISABLE,
        .pull_up_en = true,
        .pull_down_en = false,
    };
    gpio_config(&boot_button_config);

    const tinyusb_config_t tusb_cfg = {
        .device_descriptor = NULL,
        .string_descriptor = NULL,
        .external_phy = false,
        .configuration_descriptor = hid_configuration_descriptor,
    };
    tinyusb_driver_install(&tusb_cfg);

    while (1) {
        if (tud_mounted()) {
            uint32_t key_code;
           // xSemaphoreTake(handle->keyboard_handle->mutex, portMAX_DELAY);
            receive_from_queue(handle->keyboard_handle->kbd_handle,&key_code);
            //xSemaphoreGive(handle->keyboard_handle->mutex);
            uint32_t indx = get_indx(handle->keyboard_handle->kbd_handle,key_code);
        
            
         //   xSemaphoreTake(handle->command_handle->mutex,portMAX_DELAY);
            //handle->command_handle->cmds->commands[indx];
         //   xSemaphoreGive(handle->command_handle->mutex);

            uint8_t keycode[6] = {HID_KEY_A};
            tud_hid_keyboard_report(HID_ITF_PROTOCOL_KEYBOARD, 0, keycode);
            vTaskDelay(pdMS_TO_TICKS(50));
            tud_hid_keyboard_report(HID_ITF_PROTOCOL_KEYBOARD, 0, NULL);


        }
    }
    vTaskDelete(NULL);
}


TaskHandle_t start_usb_hid_task(hid_handle_t * handle , BaseType_t priority){
    // Create task with given priority
    TaskHandle_t task_handle = NULL;
    xTaskCreatePinnedToCore(usb_hid_task, "keyboard_task", CONFIG_BT_BTU_TASK_STACK_SIZE*3/2, handle, priority, &task_handle, PRO_CPU_NUM );
    return task_handle;
}
