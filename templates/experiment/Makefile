CONTIKI={{ contiki }}
TARGET=cooja

include $(CONTIKI)/Makefile.include

run:
	java -mx512m -jar $(CONTIKI)/tools/cooja/dist/cooja.jar -hidden=simulation.csc -contiki=$(CONTIKI) & echo $$! > .$(TASK)

cooja:
	make simulation.csc & echo $$! > .$(TASK)
	rm .$(TASK)
