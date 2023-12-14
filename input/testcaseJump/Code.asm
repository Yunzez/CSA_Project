# Test Code for JAL Instruction
 1   ADDI x1 x0 5         # Set x1 = 5
 2   ADDI x2 x0 10        # Set x2 = 10
 3   JAL  x3 8            # Jump to label (8 bytes ahead) and save return address in x3
 4   NOP                  # NOP for padding (this will be skipped due to jump)
 5   NOP                  # NOP for padding (this will be skipped due to jump)
 6   NOP                  # NOP for padding (this will be skipped due to jump)
 7   NOP                  # NOP for padding (this will be skipped due to jump)
# Label (This is where the JAL jumps to)
 8   ADD  x4 x1 x2        # At label: Perform x1 + x2 and store in x4
 9   HALT                 # Halt execution


1.
00000000
01010000
00000000
10010011

2.
00000000
10100000
00000001
00010011

3.
00000000
10000000
00000001
11101111

4.
00000000
00000000
00000000
00000000

5.
00000000
00000000
00000000
00000000

6.
00000000
00000000
00000000
00000000

7.
00000000
00000000
00000000
00000000

8. 
00000000
00100000
10000010
00110011

9.
11111111
11111111
11111111
11111111