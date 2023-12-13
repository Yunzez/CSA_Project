 1   LW   x1 0(x0)      // x1 = 1
 2   ADDI x2 x1 5       // x2 = 6
 3   OR   x3 x2 x1      // OR operation between x2 and x1, x3 = 7
 4   AND  x1 x3 x2      // AND operation between x3 and x2, x1 = 6
 5   XOR  x2 x1 x3      // XOR operation between x1 and x3, x2 = 1
 6   SUB  x3 x2 x1      // Subtract x1 from x2, x3 = 1 - 6 = -5
 7   SW   x3 x0 8       // Store value in x3 to memory address 8
    HALT                 // Halt the execution


1.
00000000
00000000
00000000
10000011

2. 
00000000
01010000
10000001
00010011

3. 
00000000
00010001
01100001
10110011

4.
00000000
00100001
11110000
10110011

5. 
00000000
00110000
11000001
00110011

6.
01000000
00010001
00000001
10110011

7
00000000
00110000
00100100
00100011