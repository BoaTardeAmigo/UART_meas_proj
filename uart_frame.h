#ifndef UART_FRAME_H
#define UART_FRAME_H

#include "stm32f3xx.h" // Adjust for your MCU family if needed

/** * @brief Assigns the UART peripheral used to send the frame.
 */
void uart_frame_set_uart(UART_HandleTypeDef* huart);

/** * @brief Packs measurements into a frame and transmits it.
 * @details Frame format: [0xA5, 0x5A, Type(0x01), Length(2B), Payload(Measurments)]
 * @note This call is blocking , use it after all blocks are processed
 * and ensure DMA/IT stopped working.
 */
void uart_frame_send_measurements(void);


#endif
