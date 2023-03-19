#include "esp_err.h"

#define DELAY_CODE 0x01

#define SECONDS 0x01
#define MILLISECONDS 0x00

typedef struct _keystroke {
    uint8_t modifier;
    uint8_t key_code;
    uint16_t delay;
} KEY_STROKE;


typedef struct _key_cmd {
    uint16_t size;
    KEY_STROKE inputs [];
} KEY_CMD;


typedef struct _cmd_block{
    uint16_t size;
    KEY_CMD * commands [];
} CMD_BLOCK;

// Public Methods

esp_err_t init_storage();

esp_err_t save_cmd_block(CMD_BLOCK * blk);

CMD_BLOCK *  get_cmd_block();

void cleanup_cmd_block(CMD_BLOCK *  blk);


// Test Methods
void get_nvs_info();

void traverse_cmd_block(CMD_BLOCK *  blk);

CMD_BLOCK * malloc_cmd_block(uint16_t num_cmds);

uint8_t get_key_cmd_size( uint16_t num_keys);