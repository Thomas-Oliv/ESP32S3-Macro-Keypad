
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

const uint8_t hid_configuration_descriptor[] = {
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
    FLASHING,
    LOADING,
    DONE
} RX_STATE;

uint32_t read_short(uint8_t * buf, uint8_t index){
    return *(uint16_t*)(&buf[index]);
}

void set_short(uint8_t * buf, uint8_t index, uint16_t value){
    *(uint16_t*)(&buf[index]) = value;
}

uint32_t read_long(uint8_t * buf, uint8_t index){
    return *(uint32_t*)(&buf[index]);
}

void set_long(uint8_t * buf, uint8_t index, uint32_t value){
    *(uint32_t*)(&buf[index]) = value;
}