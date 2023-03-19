
#include "command.h"
#include "nvs_flash.h"
#include "nvs.h"

#define COMMAND_NAMESPACE "storage"
#define CMD_SIZE_KEY "cmd_size"
char key_str [] = "cmd_0";

//TODO: REWRITE
// HELPER METHODS

char * get_nvs_key(uint8_t indx){
    key_str[4] = ('a'+ indx);
    return key_str;
}

CMD_BLOCK * malloc_cmd_block(uint16_t num_cmds){
    CMD_BLOCK * blk = malloc(sizeof(CMD_BLOCK) + num_cmds*sizeof(KEY_CMD *));
    blk->size = num_cmds;
    return blk;
}

uint8_t get_key_cmd_size( uint16_t num_keys){
    return num_keys*sizeof(KEY_STROKE) +sizeof(uint16_t);
}

// PUBLIC METHODS

void cleanup_cmd_block(CMD_BLOCK *  blk){
    for(uint8_t j = 0; j < blk->size; j++)
    {
        free(blk->commands[j]);
    }
    free(blk);
}

esp_err_t init_storage(){
    return nvs_flash_init();
}

CMD_BLOCK *  get_cmd_block(){
    nvs_handle_t blob_handle;
    esp_err_t err;

    //Open NVS
    uint8_t num_commands;
    err= nvs_open(COMMAND_NAMESPACE, NVS_READONLY, &blob_handle);
    if (err != ESP_OK) return NULL;
    //Get number of commands configured
    err = nvs_get_u8(blob_handle, CMD_SIZE_KEY, &num_commands);
    if (err != ESP_OK) {
        nvs_close(blob_handle);
        return NULL;
    }
    
    // Malloc block to store commands
    CMD_BLOCK * blk = malloc_cmd_block(num_commands);
    // Iterate and malloc each key command
    uint8_t i;
    for(i = 0; i < blk->size; i++)
    {
        // Get size
        size_t req_size;
        err = nvs_get_blob(blob_handle,  get_nvs_key(i), NULL, &req_size);
        if (err != ESP_OK ) break;

        if(req_size == 0) {
            err = ESP_ERR_NVS_BASE;
            break;
        }

        // Malloc size
        uint8_t* key_cmd = malloc(req_size);
        err = nvs_get_blob(blob_handle,  get_nvs_key(i), key_cmd, &req_size);
        if (err != ESP_OK) {
            free(key_cmd);
            break;
        }
        // Add command to block
        blk->commands[i] = (KEY_CMD * )key_cmd;
        
    }
    nvs_close(blob_handle);

    //Cleanup malloc if errors
    if(err != ESP_OK){
        // We malloc'd at most i key commands
        blk->size = i;
        cleanup_cmd_block(blk);
        return NULL;
    }
    traverse_cmd_block(blk);
    return blk;
}


esp_err_t save_cmd_block(CMD_BLOCK * blk){
    nvs_handle_t blob_handle;
    esp_err_t err;
    err= nvs_open(COMMAND_NAMESPACE,NVS_READWRITE, &blob_handle);
    if (err != ESP_OK) return err;
     
    err =nvs_set_u8(blob_handle, CMD_SIZE_KEY,blk->size);
    if (err != ESP_OK){
        nvs_close(blob_handle);
        return err;
    }

    for(uint8_t i = 0; i < blk->size; i++)
    {
        err = nvs_set_blob(blob_handle,  get_nvs_key(i), blk->commands[i], get_key_cmd_size(blk->commands[i]->size));
        if (err != ESP_OK) {
            nvs_close(blob_handle);
            return err;
        }
    }

    err = nvs_commit(blob_handle);
    nvs_close(blob_handle);

    return err;
}


void traverse_cmd_block(CMD_BLOCK *  blk){
    printf("number of commands: %zu\n", blk->size);
    
    for(uint8_t i = 0; i < blk->size; i++)
    {
        printf("Command: %zu\n", i);
        printf("Number Of Keys: %zu\n", blk->commands[i]->size);
        for(int j =0; j <blk->commands[i]->size; j++ ){
            KEY_STROKE key = blk->commands[i]->inputs[j];

            printf("mod : %X  | code : %X | delay: %X\n", key.modifier, key.key_code,key.delay );
        }
        printf("\n");
    }
    
    printf("\n");
}

void get_nvs_info(){
    // Example of nvs_get_stats() to get the number of used entries and free entries:
    nvs_stats_t nvs_stats;
    nvs_get_stats(NULL, &nvs_stats);
    printf("Count: UsedEntries = (%d), FreeEntries = (%d), AllEntries = (%d)\n",
        nvs_stats.used_entries, nvs_stats.free_entries, nvs_stats.total_entries);

    
    // Example of listing all the key-value pairs of any type under specified partition and namespace
    nvs_iterator_t it = NULL;
    esp_err_t res = nvs_entry_find("nvs",COMMAND_NAMESPACE, NVS_TYPE_ANY, &it);

    if(res != ESP_OK) {
        printf("find entry err: %zu\n", res);
    }

    while(res == ESP_OK) {
        nvs_entry_info_t info;
        nvs_entry_info(it, &info); // Can omit error check if parameters are guaranteed to be non-NULL
        printf("key '%s', type '%d' \n", info.key, info.type);
        res = nvs_entry_next(&it);
    }

    nvs_release_iterator(it);
    printf("\n");
}
