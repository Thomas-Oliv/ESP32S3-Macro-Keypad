
#include "usb_hid.h"
#include <stdlib.h>
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "tinyusb.h"
#include "class/hid/hid_device.h"
#include "tusb_cdc_acm.h"
#include "sdkconfig.h"

/* TINY USB SETUP  */ 
#define USB_VID   0x303A
#define USB_PID   0x4002
#define USB_BCD   0x0200

#define TUSB_DESC_TOTAL_LEN      (TUD_CONFIG_DESC_LEN +TUD_HID_DESC_LEN)
#define VBUS_MONITORING_GPIO_NUM (GPIO_NUM_0)

const uint8_t hid_report_descriptor[] = {TUD_HID_REPORT_DESC_KEYBOARD(HID_REPORT_ID(HID_ITF_PROTOCOL_KEYBOARD))};

static const uint8_t hid_configuration_descriptor[] = {
    // Configuration number, interface count, string index, total length, attribute, power in mA
    TUD_CONFIG_DESCRIPTOR(1, 1, 0, TUSB_DESC_TOTAL_LEN, TUSB_DESC_CONFIG_ATT_REMOTE_WAKEUP, 100),

    // Interface number, string index, boot protocol, report descriptor len, EP In address, size & polling interval
    TUD_HID_DESCRIPTOR(0, 2, HID_ITF_PROTOCOL_NONE, sizeof(hid_report_descriptor), 0x83, 16, 10),
};

/* TINY USB HID Callbacks */

uint8_t const *tud_hid_descriptor_report_cb(uint8_t instance)
{
     (void) instance;
    return hid_report_descriptor;
}

uint16_t tud_hid_get_report_cb(uint8_t instance, uint8_t report_id, hid_report_type_t report_type, uint8_t* buffer, uint16_t reqlen)
{
  (void) instance;
  (void) report_id;
  (void) report_type;
  (void) buffer;
  (void) reqlen;
  return 0;
}

void tud_hid_set_report_cb(uint8_t instance, uint8_t report_id, hid_report_type_t report_type, uint8_t const* buffer, uint16_t bufsize)
{
}

/* TINY USB CDC Callbacks */

static uint8_t buf[CONFIG_TINYUSB_CDC_RX_BUFSIZE + 1];
void tinyusb_cdc_rx_callback(int itf, cdcacm_event_t *event)
{
    /* initialization */
    size_t rx_size = 0;

    /* read */
    esp_err_t ret = tinyusb_cdcacm_read(itf, buf, CONFIG_TINYUSB_CDC_RX_BUFSIZE, &rx_size);
    /* write back */
    tinyusb_cdcacm_write_queue(itf, buf, rx_size);
    tinyusb_cdcacm_write_flush(itf, 0);
}


static void usb_task(void * parameter)
{
    hid_handle_t * handle = (hid_handle_t* )parameter;
    // Initialize button that will trigger HID reports
    const gpio_config_t vbus_gpio_config = {
        .pin_bit_mask = BIT64(VBUS_MONITORING_GPIO_NUM),
        .mode = GPIO_MODE_INPUT,
        .intr_type = GPIO_INTR_DISABLE,
        .pull_up_en = true,
        .pull_down_en = false,
    };
    gpio_config(&vbus_gpio_config);

    const tinyusb_config_t hid_confg = {
        .device_descriptor =NULL,
        .string_descriptor =NULL,
        .external_phy = false,
        .configuration_descriptor = hid_configuration_descriptor,
    };
    tinyusb_driver_install(&hid_confg);

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


TaskHandle_t start_usb_task(hid_handle_t * handle , BaseType_t priority){
    // Create task with given priority
    TaskHandle_t task_handle = NULL;
    xTaskCreatePinnedToCore(usb_task, "usb_task", CONFIG_BT_BTU_TASK_STACK_SIZE*3/2, handle, priority, &task_handle, PRO_CPU_NUM );
    return task_handle;
}
