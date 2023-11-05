# CSA_Project

This repository contains the implementation of a single-stage instruction cycle simulator and a five-stage instruction cycle simulater for educational purposes for **CSA** class at NYU. The simulator is designed to model the behavior of a simplified CPU as it processes instructions.

## Single-Stage Simulator:

The single-stage simulator encapsulates the entire instruction cycle in a unified stage, different from multi-stage (pipelined) simulators where each stage of instruction processing (Fetch, Decode, Execute, Memory Access, and Write Back) is distinctly separated. This approach is advantageous for understanding the basics of instruction processing without the added complexity of pipeline stages.

### State Representation:

The simulator's state is encapsulated by the `State` class, which holds the data and control flags for different segments of the instruction cycle. The naming convention within the state is such that words starting with a capital letter are actual data values, whereas all-lowercase names represent control flags.

- `IF` (Instruction Fetch): Contains the `PC` (Program Counter), which points to the next instruction to be executed, and a `nop` flag to indicate if the fetch stage should be bypassed.
- `ID` (Instruction Decode): Stores the instruction currently being decoded and a `nop` flag for skipping the stage if necessary.
- `EX` (Execute): Holds the operands, immediate value, register addresses, control flags for memory access, ALU operation codes, and the write enable signal.
- `MEM` (Memory Access): Captures the result of the ALU operation, data to be stored in memory, involved registers, and control flags for read/write operations.
- `WB` (Write Back): Contains the data to be written back to registers, target register addresses, and the write enable signal inherited from the `MEM` stage.

The `MEM` stage contains a `wrt_enable` flag, which is wholly inherited by the `WB` stage. As this CPU simulation only includes store word (`SW`) operations that necessitate a write enable switch during the `MEM` stage, the flag is only relevant here and is passed through to the `WB` stage unchanged.

### Decoder:

The decoder is a vital part of the simulator that interprets hexadecimal instructions and outputs a 32-bit binary representation. This binary is further dissected into its constituent parts for processing.


