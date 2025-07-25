/*
 * Copyright (c) 2019 Christian Taedcke <hacking@taedcke.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#define DT_DRV_COMPAT silabs_usart_spi

#define LOG_LEVEL CONFIG_SPI_LOG_LEVEL
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(spi_silabs_usart);
#include "spi_context.h"

#include <zephyr/sys/sys_io.h>
#include <zephyr/device.h>
#include <zephyr/drivers/spi.h>
#include <zephyr/drivers/spi/rtio.h>
#include <soc.h>

#include "em_cmu.h"
#include "em_usart.h"

#include <stdbool.h>

#ifdef CONFIG_PINCTRL
#include <zephyr/drivers/pinctrl.h>
#else
#ifndef CONFIG_SOC_GECKO_HAS_INDIVIDUAL_PIN_LOCATION
#error "Individual pin location support is required"
#endif
#endif /* CONFIG_PINCTRL */

#ifdef CONFIG_CLOCK_CONTROL
#include <zephyr/drivers/clock_control.h>
#include <zephyr/drivers/clock_control/clock_control_silabs.h>
#define GET_USART_CLOCK(idx)                            \
	.clock_dev = DEVICE_DT_GET(DT_INST_CLOCKS_CTLR(idx)), \
	.clock_cfg = SILABS_DT_INST_CLOCK_CFG(idx),
#elif DT_NODE_HAS_PROP(n, peripheral_id)
#define CLOCK_USART(id) _CONCAT(cmuClock_USART, id)
#define GET_USART_CLOCK(n) \
	.clock = CLOCK_USART(DT_INST_PROP(n, peripheral_id)),
#else
#if (USART_COUNT == 1)
#define CLOCK_USART(ref)	(((ref) == USART0) ? cmuClock_USART0 \
			       : -1)
#elif (USART_COUNT == 2)
#define CLOCK_USART(ref)	(((ref) == USART0) ? cmuClock_USART0 \
			       : ((ref) == USART1) ? cmuClock_USART1 \
			       : -1)
#elif (USART_COUNT == 3)
#define CLOCK_USART(ref)	(((ref) == USART0) ? cmuClock_USART0 \
			       : ((ref) == USART1) ? cmuClock_USART1 \
			       : ((ref) == USART2) ? cmuClock_USART2 \
			       : -1)
#elif (USART_COUNT == 4)
#define CLOCK_USART(ref)	(((ref) == USART0) ? cmuClock_USART0 \
			       : ((ref) == USART1) ? cmuClock_USART1 \
			       : ((ref) == USART2) ? cmuClock_USART2 \
			       : ((ref) == USART3) ? cmuClock_USART3 \
			       : -1)
#elif (USART_COUNT == 5)
#define CLOCK_USART(ref)	(((ref) == USART0) ? cmuClock_USART0 \
			       : ((ref) == USART1) ? cmuClock_USART1 \
			       : ((ref) == USART2) ? cmuClock_USART2 \
			       : ((ref) == USART3) ? cmuClock_USART3 \
			       : ((ref) == USART4) ? cmuClock_USART4 \
			       : -1)
#elif (USART_COUNT == 6)
#define CLOCK_USART(ref)	(((ref) == USART0) ? cmuClock_USART0 \
			       : ((ref) == USART1) ? cmuClock_USART1 \
			       : ((ref) == USART2) ? cmuClock_USART2 \
			       : ((ref) == USART3) ? cmuClock_USART3 \
			       : ((ref) == USART4) ? cmuClock_USART4 \
			       : ((ref) == USART5) ? cmuClock_USART5 \
			       : -1)
#else
#error "Undefined number of USARTs."
#endif /* USART_COUNT */
#define GET_USART_CLOCK(id) \
	.clock = CLOCK_USART((USART_TypeDef *)DT_INST_REG_ADDR(id)),
#endif /* DT_NODE_HAS_PROP(n, peripheral_id) */


#define SPI_WORD_SIZE 8

/* Structure Declarations */

struct spi_silabs_usart_data {
	struct spi_context ctx;
};

struct spi_silabs_usart_config {
	USART_TypeDef *base;
#ifdef CONFIG_CLOCK_CONTROL
	const struct device *clock_dev;
	const struct silabs_clock_control_cmu_config clock_cfg;
#else
	CMU_Clock_TypeDef clock;
#endif
	uint32_t clock_frequency;
#ifdef CONFIG_PINCTRL
	const struct pinctrl_dev_config *pcfg;
#else
	struct soc_gpio_pin pin_rx;
	struct soc_gpio_pin pin_tx;
	struct soc_gpio_pin pin_clk;
	uint8_t loc_rx;
	uint8_t loc_tx;
	uint8_t loc_clk;
#endif /* CONFIG_PINCTRL */
};


/* Helper Functions */
static int spi_config(const struct device *dev,
		      const struct spi_config *config,
		      uint16_t *control)
{
	const struct spi_silabs_usart_config *usart_config = dev->config;
	struct spi_silabs_usart_data *data = dev->data;
	mem_addr_t ctrl_reg = (mem_addr_t)&usart_config->base->CTRL;
	uint32_t spi_frequency;

#ifdef CONFIG_CLOCK_CONTROL
	int err;

	err = clock_control_get_rate(usart_config->clock_dev,
				     (clock_control_subsys_t)&usart_config->clock_cfg,
				     &spi_frequency);
	if (err) {
		return err;
	}
	/* Max supported SPI frequency is half the source clock */
	spi_frequency /= 2;
#else
	spi_frequency = CMU_ClockFreqGet(usart_config->clock) / 2;
#endif

	if (config->operation & SPI_HALF_DUPLEX) {
		LOG_ERR("Half-duplex not supported");
		return -ENOTSUP;
	}

	if (SPI_WORD_SIZE_GET(config->operation) != SPI_WORD_SIZE) {
		LOG_ERR("Word size must be %d", SPI_WORD_SIZE);
		return -ENOTSUP;
	}

	if (config->operation & SPI_CS_ACTIVE_HIGH) {
		sys_set_bit(ctrl_reg, _USART_CTRL_CSINV_SHIFT);
	} else {
		sys_clear_bit(ctrl_reg, _USART_CTRL_CSINV_SHIFT);
	}

	if (IS_ENABLED(CONFIG_SPI_EXTENDED_MODES) &&
	    (config->operation & SPI_LINES_MASK) != SPI_LINES_SINGLE) {
		LOG_ERR("Only supports single mode");
		return -ENOTSUP;
	}

	if (config->operation & SPI_TRANSFER_LSB) {
		sys_clear_bit(ctrl_reg, _USART_CTRL_MSBF_SHIFT);
	} else {
		sys_set_bit(ctrl_reg, _USART_CTRL_MSBF_SHIFT);
	}

	if (config->operation & SPI_OP_MODE_SLAVE) {
		LOG_ERR("Slave mode not supported");
		return -ENOTSUP;
	}

	/* Set frequency to the minimum of what the device supports, what the
	 * user has configured the controller to, and the max frequency for the
	 * transaction.
	 */
	if (usart_config->clock_frequency > spi_frequency) {
		LOG_ERR("SPI clock-frequency too high");
		return -EINVAL;
	}
	spi_frequency = MIN(usart_config->clock_frequency, spi_frequency);
	if (config->frequency) {
		spi_frequency = MIN(config->frequency, spi_frequency);
	}
	USART_BaudrateSyncSet(usart_config->base, 0, spi_frequency);

	/* Set Loopback */
	if (config->operation & SPI_MODE_LOOP) {
		usart_config->base->CTRL |= USART_CTRL_LOOPBK;
	} else {
		usart_config->base->CTRL &= ~USART_CTRL_LOOPBK;
	}

	/* Set CPOL */
	if (config->operation & SPI_MODE_CPOL) {
		usart_config->base->CTRL |= USART_CTRL_CLKPOL;
	} else {
		usart_config->base->CTRL &= ~USART_CTRL_CLKPOL;
	}

	/* Set CPHA */
	if (config->operation & SPI_MODE_CPHA) {
		usart_config->base->CTRL |= USART_CTRL_CLKPHA;
	} else {
		usart_config->base->CTRL &= ~USART_CTRL_CLKPHA;
	}

	/* Set word size */
	usart_config->base->FRAME = usartDatabits8
	    | USART_FRAME_STOPBITS_DEFAULT
	    | USART_FRAME_PARITY_DEFAULT;

	/* At this point, it's mandatory to set this on the context! */
	data->ctx.config = config;

	return 0;
}

static void spi_silabs_usart_send(USART_TypeDef *usart, uint8_t frame)
{
	/* Write frame to register */
	USART_Tx(usart, frame);

	/* Wait until the transfer ends */
	while (!(usart->STATUS & USART_STATUS_TXC)) {
	}
}

static uint8_t spi_silabs_usart_recv(USART_TypeDef *usart)
{
	/* Return data inside rx register */
	return (uint8_t)usart->RXDATA;
}

static bool spi_silabs_usart_transfer_ongoing(struct spi_silabs_usart_data *data)
{
	return spi_context_tx_on(&data->ctx) || spi_context_rx_on(&data->ctx);
}

static inline uint8_t spi_silabs_usart_next_tx(struct spi_silabs_usart_data *data)
{
	uint8_t tx_frame = 0;

	if (spi_context_tx_buf_on(&data->ctx)) {
		tx_frame = UNALIGNED_GET((uint8_t *)(data->ctx.tx_buf));
	}

	return tx_frame;
}

static int spi_silabs_usart_shift_frames(USART_TypeDef *usart,
				  struct spi_silabs_usart_data *data)
{
	uint8_t tx_frame;
	uint8_t rx_frame;

	tx_frame = spi_silabs_usart_next_tx(data);
	spi_silabs_usart_send(usart, tx_frame);
	spi_context_update_tx(&data->ctx, 1, 1);

	rx_frame = spi_silabs_usart_recv(usart);

	if (spi_context_rx_buf_on(&data->ctx)) {
		UNALIGNED_PUT(rx_frame, (uint8_t *)data->ctx.rx_buf);
	}
	spi_context_update_rx(&data->ctx, 1, 1);
	return 0;
}


static void spi_silabs_usart_xfer(const struct device *dev,
			   const struct spi_config *config)
{
	int ret;
	struct spi_silabs_usart_data *data = dev->data;
	struct spi_context *ctx = &data->ctx;
	const struct spi_silabs_usart_config *usart_config = dev->config;

	spi_context_cs_control(ctx, true);

	do {
		ret = spi_silabs_usart_shift_frames(usart_config->base, data);
	} while (!ret && spi_silabs_usart_transfer_ongoing(data));

	spi_context_cs_control(ctx, false);
	spi_context_complete(ctx, dev, 0);
}

#ifndef CONFIG_PINCTRL
static void spi_silabs_usart_init_pins(const struct device *dev)
{
	const struct spi_silabs_usart_config *config = dev->config;

	GPIO_PinModeSet(config->pin_rx.port, config->pin_rx.pin,
			 config->pin_rx.mode, config->pin_rx.out);
	GPIO_PinModeSet(config->pin_tx.port, config->pin_tx.pin,
			 config->pin_tx.mode, config->pin_tx.out);
	GPIO_PinModeSet(config->pin_clk.port, config->pin_clk.pin,
			 config->pin_clk.mode, config->pin_clk.out);

	/* disable all pins while configuring */
	config->base->ROUTEPEN = 0;

	config->base->ROUTELOC0 =
		(config->loc_tx << _USART_ROUTELOC0_TXLOC_SHIFT) |
		(config->loc_rx << _USART_ROUTELOC0_RXLOC_SHIFT) |
		(config->loc_clk << _USART_ROUTELOC0_CLKLOC_SHIFT);

	config->base->ROUTELOC1 = _USART_ROUTELOC1_RESETVALUE;

	config->base->ROUTEPEN = USART_ROUTEPEN_RXPEN | USART_ROUTEPEN_TXPEN |
		USART_ROUTEPEN_CLKPEN;
}
#endif /* !CONFIG_PINCTRL */


/* API Functions */

static int spi_silabs_usart_init(const struct device *dev)
{
	int err;
	const struct spi_silabs_usart_config *config = dev->config;
	struct spi_silabs_usart_data *data = dev->data;
	USART_InitSync_TypeDef usartInit = USART_INITSYNC_DEFAULT;

	/* The peripheral and gpio clock are already enabled from soc and gpio
	 * driver
	 */

	usartInit.enable = usartDisable;
	usartInit.baudrate = 1000000;
	usartInit.databits = usartDatabits8;
	usartInit.master = 1;
	usartInit.msbf = 1;
	usartInit.clockMode = usartClockMode0;
#if defined(USART_INPUT_RXPRS) && defined(USART_TRIGCTRL_AUTOTXTEN)
	usartInit.prsRxEnable = 0;
	usartInit.prsRxCh = 0;
	usartInit.autoTx = 0;
#endif

	/* Enable USART clock */
#ifdef CONFIG_CLOCK_CONTROL
	err = clock_control_on(config->clock_dev, (clock_control_subsys_t)&config->clock_cfg);
	if (err < 0 && err != -EALREADY) {
		return err;
	}
#else
	CMU_ClockEnable(config->clock, true);
#endif

	/* Init USART */
	USART_InitSync(config->base, &usartInit);

#ifdef CONFIG_PINCTRL
	err = pinctrl_apply_state(config->pcfg, PINCTRL_STATE_DEFAULT);
	if (err < 0) {
		return err;
	}
#else
	/* Initialize USART pins */
	spi_silabs_usart_init_pins(dev);
#endif /* CONFIG_PINCTRL */

	err = spi_context_cs_configure_all(&data->ctx);
	if (err < 0) {
		return err;
	}

	/* Enable the peripheral */
	config->base->CMD = (uint32_t) usartEnable;

	spi_context_unlock_unconditionally(&data->ctx);

	return 0;
}

static int spi_silabs_usart_transceive(const struct device *dev,
				const struct spi_config *config,
				const struct spi_buf_set *tx_bufs,
				const struct spi_buf_set *rx_bufs)
{
	struct spi_silabs_usart_data *data = dev->data;
	uint16_t control = 0;
	int ret;

	spi_context_lock(&data->ctx, false, NULL, NULL, config);

	ret = spi_config(dev, config, &control);
	if (ret < 0) {
		spi_context_release(&data->ctx, ret);
		return ret;
	}

	spi_context_buffers_setup(&data->ctx, tx_bufs, rx_bufs, 1);
	spi_silabs_usart_xfer(dev, config);

	spi_context_release(&data->ctx, ret);

	return 0;
}

#ifdef CONFIG_SPI_ASYNC
static int spi_silabs_usart_transceive_async(const struct device *dev,
				      const struct spi_config *config,
				      const struct spi_buf_set *tx_bufs,
				      const struct spi_buf_set *rx_bufs,
				      struct k_poll_signal *async)
{
	return -ENOTSUP;
}
#endif /* CONFIG_SPI_ASYNC */

static int spi_silabs_usart_release(const struct device *dev,
			     const struct spi_config *config)
{
	struct spi_silabs_usart_data *data = dev->data;

	spi_context_unlock_unconditionally(&data->ctx);

	return 0;
}

/* Device Instantiation */
static DEVICE_API(spi, spi_silabs_usart_api) = {
	.transceive = spi_silabs_usart_transceive,
#ifdef CONFIG_SPI_ASYNC
	.transceive_async = spi_silabs_usart_transceive_async,
#endif /* CONFIG_SPI_ASYNC */
#ifdef CONFIG_SPI_RTIO
	.iodev_submit = spi_rtio_iodev_default_submit,
#endif
	.release = spi_silabs_usart_release,
};

#ifdef CONFIG_PINCTRL
#define SPI_INIT(n)				    \
	PINCTRL_DT_INST_DEFINE(n);			    \
	static struct spi_silabs_usart_data spi_silabs_usart_data_##n = { \
		SPI_CONTEXT_INIT_LOCK(spi_silabs_usart_data_##n, ctx), \
		SPI_CONTEXT_INIT_SYNC(spi_silabs_usart_data_##n, ctx), \
		SPI_CONTEXT_CS_GPIOS_INITIALIZE(DT_DRV_INST(n), ctx)	\
	}; \
	static struct spi_silabs_usart_config spi_silabs_usart_cfg_##n = { \
	    .pcfg = PINCTRL_DT_INST_DEV_CONFIG_GET(n), \
	    .base = (USART_TypeDef *) \
		 DT_INST_REG_ADDR(n), \
	    GET_USART_CLOCK(n) \
	    .clock_frequency = DT_INST_PROP_OR(n, clock_frequency, 1000000) \
	}; \
	SPI_DEVICE_DT_INST_DEFINE(n, \
			spi_silabs_usart_init, \
			NULL, \
			&spi_silabs_usart_data_##n, \
			&spi_silabs_usart_cfg_##n, \
			POST_KERNEL, \
			CONFIG_SPI_INIT_PRIORITY, \
			&spi_silabs_usart_api);
#else
#define SPI_INIT(n)				    \
	static struct spi_silabs_usart_data spi_silabs_usart_data_##n = { \
		SPI_CONTEXT_INIT_LOCK(spi_silabs_usart_data_##n, ctx), \
		SPI_CONTEXT_INIT_SYNC(spi_silabs_usart_data_##n, ctx), \
		SPI_CONTEXT_CS_GPIOS_INITIALIZE(DT_DRV_INST(n), ctx)	\
	}; \
	static struct spi_silabs_usart_config spi_silabs_usart_cfg_##n = { \
	    .base = (USART_TypeDef *) \
		 DT_INST_REG_ADDR(n), \
	    GET_USART_CLOCK(n) \
	    .clock_frequency = DT_INST_PROP_OR(n, clock_frequency, 1000000), \
	    .pin_rx = { DT_INST_PROP_BY_IDX(n, location_rx, 1), \
			DT_INST_PROP_BY_IDX(n, location_rx, 2), \
			gpioModeInput, 1},				\
	    .pin_tx = { DT_INST_PROP_BY_IDX(n, location_tx, 1), \
			DT_INST_PROP_BY_IDX(n, location_tx, 2), \
			gpioModePushPull, 1},				\
	    .pin_clk = { DT_INST_PROP_BY_IDX(n, location_clk, 1), \
			DT_INST_PROP_BY_IDX(n, location_clk, 2), \
			gpioModePushPull, 1},				\
	    .loc_rx = DT_INST_PROP_BY_IDX(n, location_rx, 0), \
	    .loc_tx = DT_INST_PROP_BY_IDX(n, location_tx, 0), \
	    .loc_clk = DT_INST_PROP_BY_IDX(n, location_clk, 0), \
	}; \
	SPI_DEVICE_DT_INST_DEFINE(n, \
			spi_silabs_usart_init, \
			NULL, \
			&spi_silabs_usart_data_##n, \
			&spi_silabs_usart_cfg_##n, \
			POST_KERNEL, \
			CONFIG_SPI_INIT_PRIORITY, \
			&spi_silabs_usart_api);
#endif /* CONFIG_PINCTRL */

DT_INST_FOREACH_STATUS_OKAY(SPI_INIT)
