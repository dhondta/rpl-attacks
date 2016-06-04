CONTIKI={{ contiki }}
TARGET=cooja

include $(CONTIKI)/Makefile.include

run:
	java -mx512m -jar $(CONTIKI)/tools/cooja/dist/cooja.jar -hidden=simulation.csc -contiki=$(CONTIKI)

cooja:
	make simulation.csc
