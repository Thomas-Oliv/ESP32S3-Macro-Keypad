#include "esp_err.h"

typedef struct _key_cmd {
    uint8_t size;
    uint8_t inputs [];
} KEY_CMD;


typedef struct _cmd_block{
    uint8_t size;
    KEY_CMD * commands [];
} CMD_BLOCK;

// Public Methods

esp_err_t init_storage();

esp_err_t save_cmd_block(CMD_BLOCK * blk);

CMD_BLOCK *  get_cmd_block();

void cleanup_cmd_block(CMD_BLOCK *  blk);


// Test Methods
void get_nvs_info();

CMD_BLOCK * get_dummy_cmd_block(uint8_t num_cmds, uint8_t num_keys);

void traverse_cmd_block(CMD_BLOCK *  blk);

void test_cmd();