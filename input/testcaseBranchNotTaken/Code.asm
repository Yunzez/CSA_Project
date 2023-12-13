 1   ADDI x1 x0 5       // Set x1 = 5
 2   ADDI x2 x0 3       // Set x2 = 3
 3   BEQ  x1 x2 8   // Branch to LABEL if x1 == x2
 4   ADDI x3 x0 1       // This instruction is executed as branch is not taken
 5   NOP           // Label destination, NOP for simplicity
 6   HALT                 // Halt execution

1. 
00000000
01010000
00000000
10010011

2.
00000000
00110000
00000001
00010011

3. 
00000000
00100000
10000100
01100011

4.
00000000
00010000
00000001
10010011

5.
00000000
00000000
00000000
00000000

6.
11111111
11111111
11111111
11111111