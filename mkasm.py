#!/usr/bin/env python3

# Copyrigth (c) 2023 Mathias Panzenböck

import os
import sys
from subprocess import run, PIPE

def escape_str(data: bytes) -> str:
	index = 0
	n = len(data)
	buf: list[str] = []
	while index < n:
		prev = index
		while index < n:
			byte = data[index]
			if byte < ord(' ') or byte in (ord('"'), ord('\\')) or byte >= 0x7F:
				break
			index += 1
		if index > prev:
			chars = data[prev:index].decode('ASCII')
			if buf:
				buf.append(',')
			buf.append('"')
			buf.append(chars)
			buf.append('"')
		if index < n:
			byte = data[index]
			index += 1
			if buf:
				buf.append(',')
			buf.append(str(byte))
	return ''.join(buf)

SYS_WRITE =  1
SYS_EXIT  = 60
STDOUT    =  1

def make_asm(code: bytes, index: int) -> str:
	return f"""\
global _start

SYS_WRITE equ  1
SYS_EXIT  equ 60
STDOUT    equ  1
INDEX     equ {index}
TAIL_SIZE equ {len(code) - index}
CODE_SIZE equ {len(code)}
CODE      db  {escape_str(code)}

_start:
	mov rax, SYS_WRITE
	mov rdi, STDOUT
	mov rsi, CODE
	mov rdx, INDEX
	syscall
	push rax

	mov rax, SYS_WRITE
	mov rdi, STDOUT
	mov rsi, CODE
	mov rdx, CODE_SIZE
	syscall
	push rax

	mov rax, SYS_WRITE
	mov rdi, STDOUT
	mov rsi, CODE
	add rsi, INDEX
	mov rdx, TAIL_SIZE
	syscall
	push rax

	mov rax, SYS_EXIT
	mov rdi, 0
	syscall
"""

def read(filename: str) -> bytes:
	with open(filename, "rb") as fp:
		return fp.read()

def write(filename: str, data: bytes) -> None:
	with open(filename, "wb") as fp:
		fp.write(data)

def assemble(name: str, code: str) -> bytes:
	write(f"{name}.asm", code.encode())
	run(["nasm", "-felf64", f"{name}.asm", "-o", f"{name}.o"], check=True)
	run(["ld", f"{name}.o", "-o", name], check=True)
	run(["strip", "--strip-all", name], check=True)
	return read(name)

def main() -> None:
	# size of mark was found by trail and error
	# it infuences padding or something
	# with this size it gets the same padding as the generated code
	# but in case it changes we can just try a few sizes
	hint = 1
	max_padding = 7
	os.makedirs('build', exist_ok=True)
	for padding in range(hint, max_padding + hint):
		mark = b"<<<<CODE_MARKER" + (b"!" * padding) + b">>>>"
		asm = make_asm(mark, len(mark) - 3)
		marked_binary = assemble("build/marked-binary", asm)
		index = marked_binary.find(mark, 1)

		code = b'<' + (b'X' * (len(marked_binary) - len(mark) - 2)) + b'>'

		asm = make_asm(code, index)
		intermediate_binary = assemble("build/intermediate-binary", asm)

		index = intermediate_binary.find(code, 1)
		head = intermediate_binary[:index]
		tail = intermediate_binary[index + len(code):]

#		assemble("assembled-quine", make_asm(head + tail, index))

		binary = head + head + tail + tail
		write("build/quine", binary)
		os.chmod("build/quine", 0o755)

		pipe = run(["build/quine"], stdout=PIPE, check=True)
		out_binary = pipe.stdout

		write("build/quine.out", out_binary)
		os.chmod("build/quine.out", 0o755)
	
		if out_binary == binary:
			iteration = padding - hint + 1
			if iteration > 1:
				print("output is the same! (iteration: %d)" % iteration)
			else:
				print("output is the same!")
			return
	
	print("ERROR: output is not the same!", file=sys.stderr)
	sys.exit(1)

if __name__ == '__main__':
	main()
