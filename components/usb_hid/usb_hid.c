
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

#define TUSB_DESC_TOTAL_LEN      (TUD_CONFIG_DESC_LEN +TUD_CDC_DESC_LEN+  TUD_HID_DESC_LEN)

enum {
    ITF_NUM_CDC=0,
    ITF_NUM_CDC_DATA,
    ITF_NUM_HID,
    ITF_NUM_TOTAL
};

enum {
    // Available USB Endpoints: 5 IN/OUT EPs and 1 IN EP
    EP_EMPTY = 0,
    EPNUM_0_CDC_NOTIF,
    EPNUM_0_CDC,
    EPNUM_HID,

};


const uint8_t hid_report_descriptor[] = {TUD_HID_REPORT_DESC_KEYBOARD(HID_REPORT_ID(HID_ITF_PROTOCOL_KEYBOARD))};

static const uint8_t hid_configuration_descriptor[] = {
    // Configuration number, interface count, string index, total length, attribute, power in mA
    TUD_CONFIG_DESCRIPTOR(1, ITF_NUM_TOTAL, 0, TUSB_DESC_TOTAL_LEN, TUSB_DESC_CONFIG_ATT_REMOTE_WAKEUP, 100),

    // Interface number, string index, boot protocol, report descriptor len, EP In address, size & polling interval
    TUD_CDC_DESCRIPTOR(ITF_NUM_CDC, 4, 0x80 | EPNUM_0_CDC_NOTIF, 8, EPNUM_0_CDC, 0x80 | EPNUM_0_CDC, CFG_TUD_CDC_EP_BUFSIZE),
    TUD_HID_DESCRIPTOR(ITF_NUM_HID, 5, HID_ITF_PROTOCOL_NONE, sizeof(hid_report_descriptor), 0x80 | EPNUM_HID, 16, 10),
};

char const* string_desc_arr [] =
{
  (const char[]) { 0x09, 0x04 }, // 0: is supported language is English (0x0409)
  CONFIG_TINYUSB_DESC_MANUFACTURER_STRING,        // 1: Manufacturer
  CONFIG_TINYUSB_DESC_PRODUCT_STRING,             // 2: Product
  CONFIG_TINYUSB_DESC_SERIAL_STRING,              // 3: Serials, should use chip ID
  CONFIG_TINYUSB_DESC_CDC_STRING,                 // 4: CDC Interface
  "Macro Keypad"
};

//TODO: TRY TO FIX THIS?!
tusb_desc_device_t const descriptor_config = {
    .bLength = sizeof(descriptor_config),
    .bDescriptorType = TUSB_DESC_DEVICE,
    .bcdUSB = USB_BCD,

    .bDeviceClass = TUSB_CLASS_MISC,
    .bDeviceSubClass = MISC_SUBCLASS_COMMON,
    .bDeviceProtocol = MISC_PROTOCOL_IAD,
    .bMaxPacketSize0 = CFG_TUD_ENDPOINT0_SIZE,

    .idVendor = USB_VID, // This is Espressif VID. This needs to be changed according to Users / Customers
    .idProduct = USB_PID,
    .bcdDevice = CONFIG_TINYUSB_DESC_BCD_DEVICE,
    .iManufacturer = 0x01,
    .iProduct = 0x02,
    .iSerialNumber = 0x03,
    .bNumConfigurations = 0x01
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

typedef enum {
    IDLE=0,
    RECEIVING,
} RX_STATE;


uint8_t state;
/* TINY USB CDC Callbacks */

static uint8_t buf[CONFIG_TINYUSB_CDC_RX_BUFSIZE + 1];
void tinyusb_cdc_rx_callback(int itf, cdcacm_event_t *event)
{
    /* initialization */
    size_t rx_size = 0;
    /* read */
    esp_err_t ret = tinyusb_cdcacm_read(itf, buf, CONFIG_TINYUSB_CDC_RX_BUFSIZE, &rx_size);

    switch(state){
        case IDLE:
            //Wait for valid message to begin receiving config data

        break;
        case RECEIVING:
            // Continue receiving

        break;
    }






    /* write back */
    tinyusb_cdcacm_write_queue(itf, buf, rx_size);
    tinyusb_cdcacm_write_flush(itf, 0);
}


static void usb_task(void * parameter)
{
    state = IDLE;
    hid_handle_t * handle = (hid_handle_t* )parameter;

    const tinyusb_config_t tusb_cfg = {
        .device_descriptor =&descriptor_config,
        .string_descriptor =string_desc_arr,
        .string_descriptor_count = sizeof(string_desc_arr) / sizeof(string_desc_arr[0]),
        .external_phy = false,
        .configuration_descriptor = hid_configuration_descriptor,
        //.self_powered = true,
        //.vbus_monitor_io = VBUS_MONITORING_GPIO_NUM,
    };
    tinyusb_driver_install(&tusb_cfg);

    
    tinyusb_config_cdcacm_t acm_cfg = {
        .usb_dev = TINYUSB_USBDEV_0,
        .cdc_port = TINYUSB_CDC_ACM_0,
        .rx_unread_buf_sz = CONFIG_TINYUSB_CDC_RX_BUFSIZE,
        .callback_rx = &tinyusb_cdc_rx_callback,
        .callback_rx_wanted_char = NULL,
        .callback_line_state_changed = NULL,
        .callback_line_coding_changed = NULL
    };
    tusb_cdc_acm_init(&acm_cfg);

    while (1) {
        if (tud_mounted()) {
            uint32_t key_code = UINT32_MAX;
            //TODO: Make this Threadsafe with mutex
            receive_from_queue(handle->keyboard_handle->kbd_handle,&key_code);
            if(key_code != UINT32_MAX){
                
                //TODO: Make this Threadsafe with mutex
                uint32_t indx = get_indx(handle->keyboard_handle->kbd_handle,key_code);
                
                /* TODO Get command args from index (in threadsafe manner)
                handle->command_handle->cmds.....

                write codes to tud_hid_keyboard_report :)
                */

                uint8_t keycode[6] = {HID_KEY_A+indx};
                tud_hid_keyboard_report( HID_ITF_PROTOCOL_KEYBOARD, 0, keycode);
                vTaskDelay(pdMS_TO_TICKS(50));
                tud_hid_keyboard_report( HID_ITF_PROTOCOL_KEYBOARD, 0, NULL);
            }
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
