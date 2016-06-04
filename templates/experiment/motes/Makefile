SRC=$(wildcard [!symbols]*.c)
PROGS = $(patsubst %.c,%,$(SRC))
all: $(PROGS)

CONTIKI={{ contiki }}
TARGET={{ target }}

include $(CONTIKI)/Makefile.include

CONTIKI_WITH_IPV6 = 1
UIP_CONF_IPV6=1
CFLAGS += -DUIP_IPV6_RPL

# the two following lines are aimed to reduce Contiki's size
CFLAGS += -ffunction-sections
LDFLAGS += -Wl,--gc-sections,--undefined=_reset_vector__,--undefined=InterruptVectors,--undefined=_copy_data_init__,--undefined=_clear_bss_init__,--undefined=_end_of_init__

