#include "uart_frame.h"
#include "uart_measure.h"
#include <string.h>

#define FRAME_SYNC0 0xA5
#define FRAME_SYNC1 0x5A
#define FRAME_TYPE_MEASUREMENTS 0x01

#define MAX_PAYLOAD_SIZE (UART_MEASURE_MAX_RECORDS * sizeof(uart_measure_record_t))

static UART_HandleTypeDef* huart_ptr = NULL;
static uint8_t frame_tx_buf[5 + MAX_PAYLOAD_SIZE];

void uart_frame_set_uart(UART_HandleTypeDef* hu) {
    huart_ptr = hu;
}

void uart_frame_send_measurements(void) {
    if (!huart_ptr) return;

    uint16_t meas_count;
    const uart_measure_record_t* recs = uart_measure_get_all(&meas_count);

    if (recs == NULL || meas_count == 0) return;
    if (meas_count > UART_MEASURE_MAX_RECORDS) meas_count = UART_MEASURE_MAX_RECORDS;

    uint16_t payload_len = meas_count * sizeof(uart_measure_record_t);

    frame_tx_buf[0] = FRAME_SYNC0;
    frame_tx_buf[1] = FRAME_SYNC1;
    frame_tx_buf[2] = FRAME_TYPE_MEASUREMENTS;
    frame_tx_buf[3] = (uint8_t)(payload_len & 0xFF);
    frame_tx_buf[4] = (uint8_t)((payload_len >> 8) & 0xFF);

    memcpy(&frame_tx_buf[5], recs, payload_len);

    HAL_UART_Transmit(huart_ptr, frame_tx_buf, 5 + payload_len, 1000);
    uart_measure_reset();
}
