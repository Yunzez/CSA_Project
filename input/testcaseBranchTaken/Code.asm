 1   ADDI x1, x0, 5       // Set x1 = 5
 2   ADDI x2, x0, 5       // Set x2 = 5
 3   BEQ  x1, x2, LABEL   // Branch to LABEL if x1 == x2
 4   ADDI x3, x0, 1       // This instruction is skipped if branch is taken
 5   LABEL: NOP           // Label destination, NOP for simplicity
 6   HALT                 // Halt execution


1. 
00000000
01010000
00000000
10010011

2.
00000000
01010000
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