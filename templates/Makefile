SRC=$(wildcard [!symbols]*.c)
PROGS = $(patsubst %.c,%,$(SRC))
all: $(PROGS)

CONTIKI={{ contiki }}
TARGET={{ target }}

include $(CONTIKI)/Makefile.include

CONTIKI_WITH_IPV6 = 1
UIP_CONF_IPV6=1
CFLAGS += -DUIP_IPV6_RPL

run:
	java -mx512m -jar $(CONTIKI)/tools/cooja/dist/cooja.jar -nogui=simulation.csc -contiki=$(CONTIKI)

cooja:
	make TARGET=cooja simulation.csc

