1   LW R1, R0, #0          // Load from Mem[R0+0] to R1 - Val 5
2   LW R2, R0, #4          // Load from Mem[R0+4] to R2 - Val 3
3   ADD R3, R1, R2         // R3 = R1 + R2 = 8
4   SUB R4, R1, R2         // R4 = R1 - R2 = 2
5   LW R2, R0, #16         // Load from Mem[R0+16] to R2 - Val -3
6   ADD R8, R1, R2         // R8 = R1 + R2 = 2
7   SUB R9, R1, R2         // R9 = R1 - R2 = 8
8 halt 


1.
00000000
00000000
00000000
10000011

2. 
00000000
01000000
00000001
00000011

3.
00000000
00100000
10000001
10110011

4.
01000000
00100000
10000010
00110011

5.
00000001
00000000
00000001
00000011

6.
00000000
00100000
10000100
00110011

7.
01000000
00100000
10000100
10110011