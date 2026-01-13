/*
 * uart_measure.c
 *
 *  Created on: 11 sty 2026
 *      Author: Cyprian
 */
#include "uart_measure.h"
#include "stm32f3xx.h"

static uart_measure_record_t records[UART_MEASURE_MAX_RECORDS];
static uint16_t record_count = 0;

static uint32_t comp_start_cycles = 0;
static uint32_t cpu_hz = 72000000;

typedef struct {
    uint32_t block_id;
    uint32_t input_len;
    uint32_t output_len;
    uint32_t comp_time_us;
    uint32_t tx_start_cycles;
    uint8_t  active;
} tx_slot_t;

static tx_slot_t tx_slots[UART_MEASURE_MAX_SLOT];

static inline uint32_t cycles_to_us(uint32_t cycles) {
    return (uint32_t)(((uint64_t)cycles * 1000000ULL) / cpu_hz);
}

void uart_measure_init(void) {
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT = 0;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
}

void uart_measure_set_cpu_hz(uint32_t hz) {
    cpu_hz = hz;
}

void uart_measure_comp_start(void) {
    comp_start_cycles = DWT->CYCCNT;
}

uint32_t uart_measure_comp_end(void) {
    return cycles_to_us(DWT->CYCCNT - comp_start_cycles);
}

void uart_measure_tx_blocking(uint32_t block_id, uint32_t in_len, uint32_t out_len, uint32_t c_time, uint32_t duration_cycles) {
    if (record_count >= UART_MEASURE_MAX_RECORDS) return;

    uart_measure_record_t* r = &records[record_count++];
    	r->block_id     = block_id;
    	r->input_len    = in_len;
    	r->output_len   = out_len;
    	r->comp_time_us = c_time;
    	r->tx_time_us   = cycles_to_us(duration_cycles);
}

void uart_measure_tx_start(uint8_t slot, uint32_t id, uint32_t in_len, uint32_t out_len, uint32_t c_time) {
    if (slot >= UART_MEASURE_MAX_SLOT) return;

    tx_slots[slot].block_id     = id;
    tx_slots[slot].input_len    = in_len;
    tx_slots[slot].output_len   = out_len;
    tx_slots[slot].comp_time_us = c_time;
    tx_slots[slot].tx_start_cycles = DWT->CYCCNT;
    tx_slots[slot].active = 1;
}

void uart_measure_tx_stop(uint8_t slot) {
    if (slot >= UART_MEASURE_MAX_SLOT || !tx_slots[slot].active) return;
    if (record_count >= UART_MEASURE_MAX_RECORDS) return;

    uart_measure_record_t* r = &records[record_count++];

    r->block_id     = tx_slots[slot].block_id;
    r->input_len    = tx_slots[slot].input_len;
    r->output_len   = tx_slots[slot].output_len;
    r->comp_time_us = tx_slots[slot].comp_time_us;


    r->tx_time_us   = cycles_to_us(DWT->CYCCNT - tx_slots[slot].tx_start_cycles);
    tx_slots[slot].active = 0;
}


const uart_measure_record_t* uart_measure_get_all(uint16_t* count) {
    if (count) *count = record_count;
    return records;
}

void uart_measure_reset(void) {
    record_count = 0;
    for (uint8_t i = 0; i < UART_MEASURE_MAX_SLOT; i++) {
        tx_slots[i].active = 0;
    }
}
