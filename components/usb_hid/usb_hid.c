#include "usb_base.c"
#include "crc16.c"
#include "freertos/semphr.h"

/* TINY USB CDC Callbacks */

uint8_t save_flash;
uint8_t state;
uint16_t crc;
uint32_t len;
uint8_t * write_loc;
uint32_t offset = 0;
static uint8_t buf[CONFIG_TINYUSB_CDC_RX_BUFSIZE + 1];

void tinyusb_cdc_rx_callback(int itf, cdcacm_event_t *event)
{
    /* initialization */
    size_t rx_size = 0;
    /* read */
    esp_err_t ret = tinyusb_cdcacm_read(itf, buf, CONFIG_TINYUSB_CDC_RX_BUFSIZE, &rx_size);
    if(ret == ESP_OK){
        switch(state){
            case IDLE:{
                //Wait for valid message to begin receiving config data
                if(rx_size == 8 && 0xFF01 == read_short(buf,0) && save_flash == 0){
                    len= read_long(buf, 2);
                    crc = read_short(buf,6);
                    write_loc = malloc(len);
                    if(write_loc != NULL){
                        offset = 0;
                        //Echo back input
                        tinyusb_cdcacm_write_queue(itf, buf, rx_size);
                        tinyusb_cdcacm_write_flush(itf, 0);
                        state = FLASHING;
                    }
                    else{
                        //Echo back all ones
                        set_long(buf,0,0xFFFFFFFF);
                        set_long(buf,4,0xFFFFFFFF);
                        tinyusb_cdcacm_write_queue(itf, buf, rx_size);
                        tinyusb_cdcacm_write_flush(itf, 0);
                    }
                }
                else if(rx_size == 2 && 0xFF10 == read_short(buf,0) ){
                    state = LOADING;
                }
            } break;
            case FLASHING:{
                assert(offset + rx_size <= len);
                memcpy(&(write_loc[offset]), buf, rx_size);
                offset += rx_size;
                if(offset >= len){
                    set_short(buf,0, crc_xmodem(write_loc, len));
                    tinyusb_cdcacm_write_queue(itf, buf, 2);
                    tinyusb_cdcacm_write_flush(itf, 0);
                    save_flash = 1;
                    state = IDLE;
                }
            } break;
        }
    }
}


void process_input(hid_handle_t * handle ){
    uint32_t key_code = UINT32_MAX;
    //TODO: Make this Threadsafe with mutex
    receive_from_queue(handle->keyboard_handle->kbd_handle,&key_code);
    if(key_code != UINT32_MAX){
        
        //TODO: Make this Threadsafe with mutex
        uint32_t indx = get_indx(handle->keyboard_handle->kbd_handle,key_code);
        
        xSemaphoreTake(handle->command_handle->mutex, portMAX_DELAY);
        if(handle->command_handle->cmds != NULL && indx < handle->command_handle->cmds->size ){
            KEY_CMD * cmds = handle->command_handle->cmds->commands[indx];
            for (int i =0; i < cmds->size; i++){
                KEY_STROKE press = cmds->inputs[i];
                if(press.key_code == DELAY_CODE){
                    tud_hid_keyboard_report( HID_ITF_PROTOCOL_KEYBOARD, 0, NULL);
                    if(press.modifier == MILLISECONDS){
                        vTaskDelay(press.delay);
                    }
                    else{
                        vTaskDelay(press.delay*1000);
                    }
                }
                else{
                    uint8_t keycode[6] = {press.key_code};
                    tud_hid_keyboard_report( HID_ITF_PROTOCOL_KEYBOARD, press.modifier, keycode);
                    vTaskDelay(pdMS_TO_TICKS(50));

                }
            }
            tud_hid_keyboard_report( HID_ITF_PROTOCOL_KEYBOARD, 0, NULL);
            vTaskDelay(pdMS_TO_TICKS(50));
        }
        xSemaphoreGive(handle->command_handle->mutex);
    }
}

void save_to_nvs(hid_handle_t * handle){
    xSemaphoreTake(handle->command_handle->mutex, portMAX_DELAY);
    if(handle->command_handle->cmds != NULL){
        // Cleanup old command block
        cleanup_cmd_block(handle->command_handle->cmds);
        handle->command_handle->cmds = NULL;
    }
    //Alloc new command block
    uint8_t num_commands = get_size(handle->keyboard_handle->kbd_handle);
    CMD_BLOCK * new_block = malloc_cmd_block(num_commands);
    if(new_block != NULL){
        new_block->size = num_commands;
        uint8_t offset = 0;
        for(uint8_t i =0; i < num_commands;i++){
            new_block->commands[i] = (KEY_CMD *)&(write_loc[offset]);
            offset += get_key_cmd_size(new_block->commands[i]->size);
        }
        handle->command_handle->cmds = new_block;
        handle->command_handle->action = SAVE_BLOCK;

        xSemaphoreGive(handle->command_handle->mutex);
        send_command_control(handle->command_handle, 1);
    }
    else{
        xSemaphoreGive(handle->command_handle->mutex);
        free(write_loc);
    }
    save_flash = 0;
}

static void usb_task(void * parameter)
{
    save_flash = 0;
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
            if(save_flash){
                save_to_nvs(handle);
            }
            else{
                process_input(handle);
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
