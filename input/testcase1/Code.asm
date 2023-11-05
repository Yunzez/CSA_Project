0:   LW R1, R0, #0          // Load from Mem[R0+0] to R1 - Val 5
4:   LW R2, R0, #4          // Load from Mem[R0+4] to R2 - Val 3
8:   ADD R3, R1, R2         // R3 = R1 + R2
12:  SUB R4, R1, R2         // R4 = R1 - R2
16:  SW R3, R0, #8          // Store R3 in Mem[R0+8]
20:  SW R4, R0, #12         // Store R4 in Mem[R0+12]
24:  AND R5, R1, R2 
28:  OR R6, R1, R2  
32:  XOR R7, R1, R2 
36:  LW R2, R0, #16         // Load from Mem[R0+16] to R2 - Val -3
40:  ADD R8, R1, R2         // R8 = R1 + R2
44:  SUB R9, R1, R2         // R9 = R1 - R2
58:  AND R10, R1, R2    
52:  OR R11, R1, R2 
56:  XOR R12, R1, R2    
60:  LW R1, R0, #20         // Load from Mem[R0+20] to R1 - Val -5
64:  LW R2, R0, #24         // Load from Mem[R0+24] to R2 - Val 2
68:  ADD R13, R1, R2        // R13 = R1 + R2
72:  SUB R14, R1, R2        // R14 = R1 - R2
76:  AND R15, R1, R2
80:  OR R16, R1, R2
84:  XOR R17, R1, R2
88:  ADDI R18, R2, #2047
92:  ANDI R19, R2, #2047
96:  ORI R20, R2, #2047
100: XORI R21, R2, #2047
104: ADDI R22, R1, #2047
108: ANDI R23, R1, #2047
112: ORI R24, R1, #2047
116: XORI R25, R1, #2047
120: ADDI R26, R2, #-1
124: ANDI R27, R2, #-1
128: ORI R28, R2, #-1
132: XORI R29, R2, #-1
136: ADDI R30, R1, #-1
140: ANDI R31, R1, #-1
144: ORI R31, R1, #-1
148: XORI R0, R1, #-1
152: HALT                  // Halt

/* Binary
00000000000000000000000010000011
00000000010000000000000100000011
00000000001000001000000110110011
01000000001000001000001000110011
00000000001100000010010000100011
00000000010000000010011000100011
00000000000100010111001010110011
00000000000100010110001100110011
00000000000100010100001110110011
00000001000000000000000100000011
00000000001000001000010000110011
01000000001000001000010010110011
00000000000100010111010100110011
00000000000100010110010110110011
00000000000100010100011000110011
00000001010000000000000010000011
00000001100000000000000100000011
00000000001000001000011010110011
01000000001000001000011100110011
00000000000100010111011110110011
00000000000100010110100000110011
00000000000100010100100010110011
01111111111100010000100100010011
01111111111100010111100110010011
01111111111100010110101000010011
01111111111100010100101010010011
01111111111100001000101100010011
01111111111100001111101110010011
01111111111100001110110000010011
01111111111100001100110010010011
11111111111100010000110100010011
11111111111100010111110110010011
11111111111100010110111000010011
11111111111100010100111010010011
11111111111100001000111100010011
11111111111100001111111110010011
11111111111100001110111110010011
11111111111100001100000000010011
11111111111111111111111111111111
*/