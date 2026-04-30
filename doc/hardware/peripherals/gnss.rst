.. _gnss_api:

GNSS (Global Navigation Satellite System)
#########################################

Overview
********

GNSS is a general term which covers satellite systems used for
navigation, like GPS (Global Positioning System). GNSS services
are usually accessed through GNSS modems which receive and
process GNSS signals to determine their position, or more
specifically, their antennas position. They usually
additionally provide a precise time synchronization mechanism,
commonly named PPS (Pulse-Per-Second).

Subsystem support
*****************

The GNSS subsystem is based on the :ref:`modem`. The GNSS
subsystem covers everything from sending and receiving commands
to and from the modem, to parsing, creating and processing
NMEA0183 messages.

Adding support for additional NMEA0183 based GNSS modems
requires little more than implementing power management
and configuration for the specific GNSS modem.

Adding support for GNSS modems which use other protocols and/or
buses than the usual NMEA0183 over UART is possible, but will
require a bit more work from the driver developer.

Configuration Options
*********************

Related configuration options:

* :kconfig:option:`CONFIG_GNSS`
* :kconfig:option:`CONFIG_GNSS_SATELLITES`
* :kconfig:option:`CONFIG_GNSS_ACCURACY`
* :kconfig:option:`CONFIG_GNSS_RAW_NMEA`
* :kconfig:option:`CONFIG_GNSS_DUMP_TO_LOG`

Position Accuracy
*****************

When :kconfig:option:`CONFIG_GNSS_ACCURACY` is enabled, drivers may
publish a per-fix uncertainty estimate parallel to the navigation
data callback. The estimate is carried by ``struct gnss_accuracy``
and includes per-axis (latitude / longitude / altitude) standard
deviations, the RMS of the range inputs and the error ellipse
(semi-major axis, semi-minor axis, orientation). All distances are
in millimetres; the orientation is in 1/100 degrees true north.
Values are typically derived from the NMEA GST sentence.

Consumers register a callback via
:c:macro:`GNSS_DT_ACCURACY_CALLBACK_DEFINE` and receive
:c:struct:`gnss_accuracy` instances synchronously from the publisher.
The callback split mirrors :c:struct:`gnss_data` /
:c:struct:`gnss_satellite`: drivers that do not support GST output
incur no cost from the wider type.

Raw NMEA Forwarding
*******************

When :kconfig:option:`CONFIG_GNSS_RAW_NMEA` is enabled, drivers may
forward every received NMEA sentence to a registered callback before
type-specific parsing kicks in. The callback receives a pointer +
length pair containing the byte-faithful sentence (delimiter
stripped, checksum bytes retained); the buffer is owned by the
driver and is valid only for the duration of the call. Consumers
that need to retain the bytes must copy them.

Consumers register the callback via
:c:macro:`GNSS_DT_RAW_NMEA_CALLBACK_DEFINE`. Use cases include
forensic logging and forwarding the raw stream to a downstream
peer (for example a USB CDC-ACM endpoint exposing the modem to a
host).

Navigation Reference
********************

.. doxygengroup:: navigation

GNSS API Reference
******************

.. doxygengroup:: gnss_interface
