.PHONY: all clean clean-intermediate

all: build/quine

build/quine: mkasm.py
	./mkasm.py

clean-intermediate:
	rm build/marked-binary build/marked-binary.asm build/marked-binary.o \
	   build/intermediate-binary build/intermediate-binary.asm build/intermediate-binary.o

clean: clean-intermediate
	rm build/quine build/quine.out
