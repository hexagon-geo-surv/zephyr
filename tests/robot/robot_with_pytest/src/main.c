#include <zephyr/kernel.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/sys/printk.h>
#include <zephyr/version.h>
#include <string.h>

/* Buffer for receiving commands */
static char rx_buf[256];
static int rx_buf_pos;

/* Command handlers */
static void handle_echo_command(const char *data)
{
    printk("ECHO: %s\n", data);
}

static void handle_version_command(const char *data)
{
    printk("FIRMWARE_VERSION: 1.0.0\n");
    printk("BOARD: %s\n", CONFIG_BOARD);
    printk("ZEPHYR_VERSION: %s\n", KERNEL_VERSION_STRING);
}

static void handle_help_command(const char *data)
{
    printk("Available commands:\n");
    printk("  ECHO <text>     - Echo back the text\n");
    printk("  VERSION         - Show firmware version\n");
    printk("  HELP            - Show this help\n");
}

/* Process received command */
static void process_command(const char *command)
{
    char cmd[32];
    char data[224];
    
    /* Parse command and data */
    int parsed = sscanf(command, "%31s %223[^\n]", cmd, data);
    
    if (parsed >= 1) {
        if (strcmp(cmd, "ECHO") == 0) {
            handle_echo_command(parsed >= 2 ? data : "");
        } else if (strcmp(cmd, "VERSION") == 0) {
            handle_version_command("");
        } else if (strcmp(cmd, "HELP") == 0) {
            handle_help_command("");
        } else {
            printk("UNKNOWN COMMAND: %s\n", cmd);
            printk("Type HELP for available commands\n");
        }
    }
}

/* UART interrupt callback */
static void uart_callback(const struct device *dev, void *user_data)
{
    uint8_t c;

    while (uart_irq_update(dev) && uart_irq_rx_ready(dev)) {
        uart_fifo_read(dev, &c, 1);

        if (c == '\n' || c == '\r') {
            if (rx_buf_pos > 0) {
                rx_buf[rx_buf_pos] = '\0';
                process_command(rx_buf);
                rx_buf_pos = 0;
                printk("> ");
            }
        } else if (rx_buf_pos < (sizeof(rx_buf) - 1)) {
            rx_buf[rx_buf_pos++] = c;
        }
    }
}

int main(void)
{
    const struct device *uart_dev = DEVICE_DT_GET(DT_CHOSEN(zephyr_console));
    
    /* Configure UART */
    if (!device_is_ready(uart_dev)) {
        printk("UART device not ready\n");
        return -EFAULT;
    }

    /* Configure UART callback */
    uart_irq_callback_set(uart_dev, uart_callback);
    uart_irq_rx_enable(uart_dev);

    printk("Robot Framework Test Application Started\n");
    printk("Board: %s\n", CONFIG_BOARD);
    printk("Ready for commands. Type HELP for available commands.\n");
    printk("> ");

    while (1) {
        k_sleep(K_SECONDS(1));
    }

    return 0;
}
