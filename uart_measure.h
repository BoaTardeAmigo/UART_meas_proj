/*
 * uart_measure.h
 *
 *  Created on: 11 sty 2026
 *      Author: Cyprian
 */

#ifndef UART_MEASURE_H
#define UART_MEASURE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define UART_MEASURE_MAX_RECORDS 24
#define UART_MEASURE_MAX_SLOT 2

/** * @brief Measurement record for a block of data
 * Packed attribute ensures compatibility with PC side struct.
 */
typedef struct __attribute__((packed)) {
    uint32_t block_id;
    uint32_t input_len;
    uint32_t output_len;
    uint32_t comp_time_us;
    uint32_t tx_time_us;
} uart_measure_record_t;

/* --- System --- */

/** @brief Initializes DWT cycle counter */
void uart_measure_init(void);
/** @brief Sets CPU frequency for  */
void uart_measure_set_cpu_hz(uint32_t hz);
/** @brief Resets stored measurments and active DMA slots */
void uart_measure_reset(void);
/** @brief Returns pointer to record array and updates count*/
const uart_measure_record_t* uart_measure_get_all(uint16_t* count);

/* --- Compression --- */

/** @brief Starts measuring compression cycles*/
void     uart_measure_comp_start(void);
/** @brief Stops measuring compression cycles */
uint32_t uart_measure_comp_end(void);

/* --- Transmission --- */

/** * @brief Manually logs a record for blocking transfers
 * @param  duration_cycles  DWT cycles spent in HAL_UART_Transmit.
 */
void uart_measure_tx_blocking(uint32_t block_id, uint32_t in_len, uint32_t out_len, uint32_t c_time, uint32_t duration_cycles);

/** * @brief Snapshots block metadata and starts the TX timer for that block.
 * @note Call this immediately before HAL_UART_Transmit_DMA/IT.
 */
void uart_measure_tx_start(uint8_t slot, uint32_t id, uint32_t in_len, uint32_t out_len, uint32_t c_time);
/** * @brief Stops the TX timer and saves the measurments for the block.
 * @note Call this inside HAL_UART_TxCpltCallback.
 */
void uart_measure_tx_stop(uint8_t slot);

#ifdef __cplusplus
}
#endif

#endif
