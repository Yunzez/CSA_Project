import os
import argparse

from InstructionDecoder import Decoder
from ALU import ALU
from State import State
from InstructionMem import InsMem
from DataMem import DataMem
from RegisterFile import RegisterFile

MemSize = 1000  # memory size, in reality, the memory size should be 2^32, but for this lab, for the space resaon, we keep it as this large number, but the memory is still 32-bit addressable.


def bin_to_int(binary_str):
    print('binary str:', binary_str, int(binary_str, 2))
    # Check if the number is negative (MSB is 1)
    if binary_str[0] == "1":
        # Compute negative number
        return -((int(binary_str, 2) ^ ((1 << len(binary_str)) - 1)) + 1)
    else:
        # Number is positive, so just convert to int
        return int(binary_str, 2)


class Core(object):
    def __init__(self, ioDir, imem, dmem):
        self.myRF = RegisterFile(ioDir)
        self.cycle = 0
        self.halted = False
        self.ioDir = ioDir
        self.state = State()
        self.nextState = State()
        self.ext_imem = imem
        self.ext_dmem = dmem


class SingleStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(SingleStageCore, self).__init__(ioDir + "/SS_", imem, dmem)
        self.opFilePath = ioDir + "/StateResult_SS.txt"
        print("single stage core location:", self.opFilePath)
        print("start single stage core")
        self.alu = ALU()
        self.decoder = Decoder()

    def step(self):
        print("single core steps forward")
        # 1. Instruction Fetch (IF)
        current_instruction = self.ext_imem.readInstr(self.state.IF["PC"])
        print('current pc:', self.state.IF["PC"], 'current instruction:', current_instruction)
        # * 2. Instruction Decode (ID)
        decodeResult = Decoder().decode(current_instruction)
        print("decode result:", decodeResult)
        self.state.ID["Instr"] = current_instruction
        self.state.ID["nop"] = decodeResult["type"] == "NOP"  # NOP instruction
        print("nop:", self.state.ID["nop"])

        if decodeResult["type"] == "HALT":
            self.halted = True
            return

        ALU_CONTROL_CODES = {
            "ADD": "0010",
            "SUB": "0110",
            "AND": "0000",
            "OR": "0001",
            "XOR": "0111",
            "None": "1000",
        }

        alu_control_input = ALU_CONTROL_CODES[
            "None"
        ]  # Default to ADD for initialization

        # Determine ALUOp bits
        if decodeResult["type"] == "R":
            self.state.EX["alu_op"] = "10"  # 10 for R-type instructions
        elif decodeResult["type"] == "I":
            self.state.EX["alu_op"] = "11"  # 11 for I type instructions including JAL
        elif decodeResult["type"] == "S":
            self.state.EX["alu_op"] = "00"  # 00 for store instructions (S-type)
        elif decodeResult["type"] == "B":
            self.state.EX["alu_op"] = "01"  # 01 for branch instructions (B-type)
        elif decodeResult["type"] == "J":
            self.state.EX[
                "alu_op"
            ] = "11"  # Reusing '11' for J-type, but will need special handling

        if decodeResult["type"] == "I":
            self.state.EX["is_I_type"] = True
            self.state.EX["Imm"] = decodeResult["Imm"]
            self.state.EX["Wrt_reg_addr"] = decodeResult["rd"]
            self.state.EX["Rs"] = decodeResult["rs1"]
            self.state.EX["Read_data1"] = self.myRF.readRF(decodeResult["rs1"])
        else:
            self.state.EX["is_I_type"] = False

        if decodeResult["type"] == "R":
            self.state.EX["Rs"] = decodeResult["rs1"]
            self.state.EX["Rt"] = decodeResult["rs2"]
            self.state.EX["Read_data1"] = self.myRF.readRF(decodeResult["rs1"])
            self.state.EX["Read_data2"] = self.myRF.readRF(decodeResult["rs2"])
            self.state.EX["Wrt_reg_addr"] = decodeResult["rd"]

        if decodeResult["type"] == "B":
            self.state.EX["Imm"] = decodeResult["Imm"]
            self.state.EX["Rs"] = decodeResult["rs1"]
            self.state.EX["Rt"] = decodeResult["rs2"]
            self.state.EX["Read_data1"] = self.myRF.readRF(decodeResult["rs1"])
            self.state.EX["Read_data2"] = self.myRF.readRF(decodeResult["rs2"])

        if decodeResult["type"] == "S":
            self.state.EX["Rs"] = decodeResult["rs1"]
            self.state.EX["Rt"] = decodeResult["rs2"]
            self.state.EX["Read_data1"] = self.myRF.readRF(decodeResult["rs1"])
            self.state.EX["Imm"] = decodeResult["Imm"]
            self.state.EX[
                "is_I_type"
            ] = True  # ! we need this to be true so imm is used instead of Read_data2

        if decodeResult["type"] == "J":
            self.state.EX["Imm"] = decodeResult["Imm"]
            self.state.EX["Wrt_reg_addr"] = decodeResult["rd"]
            # this will be PC + 4
            self.state.EX["Read_data1"] = self.state.IF["PC"] 
            self.state.EX["Read_data2"] = 4
            print('j type data:', self.state.EX["Read_data1"], self.state.EX["Read_data2"])

        # * 3. Execute (EX)
        self.state.EX["nop"] = self.state.ID["nop"]

        if self.state.EX["nop"]:
            pass

        # * types include S I B J R

        if self.state.EX["alu_op"] == "10":  # R-type operations
            funct3 = decodeResult["funct3"]
            if funct3 == "000":
                funct7 = decodeResult["funct7"]
                alu_control_input = (
                    ALU_CONTROL_CODES["ADD"]
                    if funct7 == "0000000"
                    else ALU_CONTROL_CODES["SUB"]
                )
            elif funct3 == "100":
                alu_control_input = ALU_CONTROL_CODES["XOR"]  # "XOR"
            elif funct3 == "110":
                alu_control_input = ALU_CONTROL_CODES["OR"]
            elif funct3 == "111":
                alu_control_input = ALU_CONTROL_CODES["ADD"]
        elif self.state.EX["alu_op"] == "11":  # I-type operations including JAL
            if decodeResult["type"] == "I":
                funct3 = decodeResult["funct3"]
                print("funct3:", funct3, funct3 == "000")
                if funct3 == "000":
                    alu_control_input = ALU_CONTROL_CODES["ADD"]  # "ADDI"
                elif funct3 == "100":
                    alu_control_input = ALU_CONTROL_CODES["XOR"]  # "XORI"
                elif funct3 == "110":
                    alu_control_input = ALU_CONTROL_CODES["OR"]  # "ORI"
                elif funct3 == "111":
                    alu_control_input = ALU_CONTROL_CODES["AND"]  # "ANDI"
            elif decodeResult["type"] == "J":
                alu_control_input = ALU_CONTROL_CODES[
                    "ADD"
                ]  # JAL will use ADD to compute the next PC
        elif self.state.EX["alu_op"] == "00":  # S-type operations (store)
            alu_control_input = ALU_CONTROL_CODES[
                "ADD"
            ]  # Store uses ADD for address calculation
        elif self.state.EX["alu_op"] == "01":  # B-type operations (branch)
            alu_control_input = ALU_CONTROL_CODES[
                "SUB"
            ]  # Branches use SUB for comparison

        print("alu operation:", alu_control_input)
        print("add imm ?", self.state.EX["is_I_type"])

        # Pass the appropriate arguments to the ALU based on the instruction type
        alu_result = None

        # print('data 1: ', self.state.EX["Read_data1"], 'data 2:', self.state.EX["Read_data2"] if self.state.EX["Read_data2"] else 0, 'imm:', self.state.EX["Imm"] if self.state.EX["Imm"] else 0 )

        if self.state.EX["is_I_type"]:
            # Convert both operands to integers
            data1 = (
                bin_to_int(self.state.EX["Read_data1"])
                if isinstance(self.state.EX["Read_data1"], str)
                else self.state.EX["Read_data1"]
            )
            imm = (
                bin_to_int(self.state.EX["Imm"])
                if isinstance(self.state.EX["Imm"], str)
                else self.state.EX["Imm"]
            )
            alu_result = self.alu.operate(
                alu_control_input,
                data1,
                imm,
            )

        else:
            data1 = (
                int(self.state.EX["Read_data1"], 2)
                if isinstance(self.state.EX["Read_data1"], str)
                else self.state.EX["Read_data1"]
            )
            data2 = (
                int(self.state.EX["Read_data2"], 2)
                if isinstance(self.state.EX["Read_data2"], str)
                else self.state.EX["Read_data2"]
            )
            alu_result = self.alu.operate(
                alu_control_input,
                data1,
                data2,
            )

        print("alu result:", alu_result)

        # ! Execute branch instructions
        if decodeResult["type"] == "B":
            if decodeResult["funct3"] == "000" and alu_result == 0:  # BEQ
                self.nextState.IF["PC"] = (
                    self.state.IF["PC"] + bin_to_int(self.state.EX["Imm"]) 
                )
                print("BEQ branch taken")
            elif decodeResult["funct3"] == "001" and alu_result != 0:  # BNE
                print(bin_to_int(self.state.EX["Imm"]))
                self.nextState.IF["PC"] = (
                    self.state.IF["PC"] + bin_to_int(self.state.EX["Imm"])  
                )
                print("BNE branch taken")
            else:
                print("branch not taken")
                self.nextState.IF["PC"] = self.state.IF["PC"] + 4
        elif decodeResult["type"] == "J":
            self.nextState.IF["PC"] = (
                self.state.IF["PC"] + bin_to_int(self.state.EX["Imm"]) 
            )

            print('j type next pc:', self.nextState.IF["PC"])
        else: 
            # PC + 1 for all instructions except branches
            self.nextState.IF["PC"] = self.state.IF["PC"] + 4


        # ! set state for next action

        # Assuming alu_result has already been computed in the execution stage
        self.state.MEM["ALUresult"] = alu_result

        # Check for Load instructions (LW)
        if decodeResult["type"] == "I" and decodeResult["opcode"] == "0000011":
            # * For LW instructions, we need to read from memory
            self.state.MEM["rd_mem"] = 1
            self.state.MEM["wrt_mem"] = 0
            self.state.MEM[
                "wrt_enable"
            ] = 1  # We will write to a register after reading from memory
            self.state.MEM["Wrt_reg_addr"] = self.state.EX[
                "Wrt_reg_addr"
            ]  # The destination register

        # Check for Store instructions (SW)
        elif decodeResult["type"] == "S" and decodeResult["opcode"] == "0100011":
            # * For SW instructions, we need to write to memory
            rs2_index = decodeResult["rs2"]
            store_data = self.myRF.readRF(rs2_index)
            self.state.MEM["rd_mem"] = 0
            self.state.MEM["wrt_mem"] = 1
            self.state.MEM["Store_data"] = store_data  # Data to be stored
            print('store data:', store_data)
            self.state.MEM["wrt_enable"] = 0
            # In the case of store, we don't write to the register file, so wrt_enable is False

        # Check for R-type instructions (like ADD, SUB, etc.)
        elif decodeResult["type"] == "R":
            # For R-type instructions, no memory operation is needed
            self.state.MEM["rd_mem"] = 0
            self.state.MEM["wrt_mem"] = 0
            self.state.MEM[
                "wrt_enable"
            ] = 1  # We will write the ALU result to a register
            self.state.MEM["Wrt_reg_addr"] = self.state.EX[
                "Wrt_reg_addr"
            ]  # The destination register

        # Check for I-type instructions that are not LW (like ADDI, ANDI, etc.)
        elif decodeResult["type"] == "I" and decodeResult["opcode"] != "0000011":
            # For these I-type instructions, no memory operation is needed
            self.state.MEM["rd_mem"] = 0
            self.state.MEM["wrt_mem"] = 0
            self.state.MEM[
                "wrt_enable"
            ] = True  # We will write the ALU result to a register
            self.state.MEM["Wrt_reg_addr"] = self.state.EX[
                "Wrt_reg_addr"
            ]  # The destination register

        # Check for B-type instructions (Branches)
        elif decodeResult["type"] == "B":
            # For branch instructions, no memory operation is needed and no write to the register file
            self.state.MEM["rd_mem"] = 0
            self.state.MEM["wrt_mem"] = 0
            self.state.MEM["wrt_enable"] = 0

        # Check for J-type instructions (like JAL)
        elif decodeResult["type"] == "J":
            # For JAL instructions, no memory operation is needed
            self.state.MEM["rd_mem"] = 0
            self.state.MEM["wrt_mem"] = 0
            self.state.MEM["wrt_enable"] = 1  # We will write the PC+4 to a register
            self.state.MEM["Wrt_reg_addr"] = self.state.EX[
                "Wrt_reg_addr"
            ]  # The destination register

        self.state.MEM["Rs"] = self.state.EX["Rs"]  # Source register 1
        self.state.MEM["Rt"] = self.state.EX[
            "Rt"
        ]  # Source register 2 or destination for stores

        # * 4. Memory Access (MEM)
        # ... if it's a load/store, access memory ...
        self.state.MEM["nop"] = self.state.ID["nop"]
        if self.state.MEM["nop"]:
            pass

        # Load Instruction
        elif self.state.MEM["rd_mem"]:
            # Calculate the memory address to read from
            mem_address = self.state.MEM["ALUresult"]
            # Access the memory and read the data
            read_data = self.ext_dmem.readInstr(mem_address)
            # Save the read data for the Write Back (WB) stage
            print("load type instruction, read memory from", mem_address)
            self.state.WB["Wrt_data"] = read_data

        # * Store Instruction
        # * store will not need to write back
        elif self.state.MEM["wrt_mem"]:
            # Calculate the memory address to write to
            mem_address = bin(self.state.MEM["ALUresult"])
            # Data to be stored in memory comes from the second register (Rt)
            store_data = self.state.MEM["Store_data"]
            print(
                "store data:",
                store_data,
                "to address:",
                mem_address,
                " ",
                int(mem_address, 2),
                "in memory",
            )
            # Write the data to memory
            self.ext_dmem.writeDataMem(int(mem_address, 2), store_data)

        else:
            self.state.WB["Wrt_data"] = self.state.MEM["ALUresult"]

        # * update the state for next action
        # True for load (rd_mem) instructions and any R-type or I-type instructions
        # For store instructions (wrt_mem), it should be False
        self.state.WB["wrt_enable"] = self.state.MEM["wrt_enable"]
        self.state.WB["nop"] = self.state.ID["nop"]

        self.state.WB["Wrt_reg_addr"] = self.state.MEM["Wrt_reg_addr"]
        self.state.WB["Rs"] = self.state.MEM["Rs"]
        self.state.WB["Rt"] = self.state.MEM["Rt"]

        # * 5. Write Back (WB)
        if self.state.WB["nop"] == True:
            pass

        elif self.state.WB["wrt_enable"]:
            data = self.state.WB["Wrt_data"]
            self.myRF.writeRF(self.state.WB["Wrt_reg_addr"], data)

        else:
            pass

        if self.state.IF["nop"]:
            self.nextState.IF["nop"] = self.state.IF["nop"]
            self.halted = True

        self.myRF.outputRF(self.cycle)  # dump RF
        self.printState(
            self.nextState, self.cycle
        )  # print states after executing cycle 0, cycle 1, cycle 2 ...

        self.state = (
            self.nextState
        )  # The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = [
            "-" * 70 + "\n",
            "State after executing cycle: " + str(cycle) + "\n",
        ]
        printstate.append("IF.PC: " + str(state.IF["PC"] ) + "\n")
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")

        if cycle == 0:
            perm = "w"
        else:
            perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)


class FiveStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(FiveStageCore, self).__init__(ioDir + "\\FS_", imem, dmem)
        self.opFilePath = ioDir + "\\StateResult_FS.txt"

    def step(self):
        # Your implementation
        # --------------------- WB stage ---------------------

        # --------------------- MEM stage --------------------

        # --------------------- EX stage ---------------------

        # --------------------- ID stage ---------------------

        # --------------------- IF stage ---------------------

        self.halted = True
        if (
            self.state.IF["nop"]
            and self.state.ID["nop"]
            and self.state.EX["nop"]
            and self.state.MEM["nop"]
            and self.state.WB["nop"]
        ):
            self.halted = True

        self.myRF.outputRF(self.cycle)  # dump RF
        self.printState(
            self.nextState, self.cycle
        )  # print states after executing cycle 0, cycle 1, cycle 2 ...

        self.state = (
            self.nextState
        )  # The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = [
            "-" * 70 + "\n",
            "State after executing cycle: " + str(cycle) + "\n",
        ]
        printstate.extend(
            ["IF." + key + ": " + str(val) + "\n" for key, val in state.IF.items()]
        )
        printstate.extend(
            ["ID." + key + ": " + str(val) + "\n" for key, val in state.ID.items()]
        )
        printstate.extend(
            ["EX." + key + ": " + str(val) + "\n" for key, val in state.EX.items()]
        )
        printstate.extend(
            ["MEM." + key + ": " + str(val) + "\n" for key, val in state.MEM.items()]
        )
        printstate.extend(
            ["WB." + key + ": " + str(val) + "\n" for key, val in state.WB.items()]
        )

        if cycle == 0:
            perm = "w"
        else:
            perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)


if __name__ == "__main__":
    # parse arguments for input file location
    parser = argparse.ArgumentParser(description="RV32I processor")
    parser.add_argument(
        "--iodir", default="", type=str, help="Directory containing the input files."
    )
    args = parser.parse_args()

    ioDir = os.path.abspath(args.iodir)
    print("IO Directory:", ioDir)

    imem = InsMem("Imem", ioDir)
    dmem_ss = DataMem("SS", ioDir)
    dmem_fs = DataMem("FS", ioDir)

    ssCore = SingleStageCore(ioDir, imem, dmem_ss)
    fsCore = FiveStageCore(ioDir, imem, dmem_fs)

    while True:
        if not ssCore.halted:
            ssCore.step()
            print("=" * 20)

        # ! open the five step core later
        # if not fsCore.halted:
        #     print("step")
        #     fsCore.step()

        # ! change to and statement later
        if ssCore.halted or fsCore.halted:
            print("Finished simulation.")
            break

    # dump SS and FS data mem.
    dmem_ss.outputDataMem()
    dmem_fs.outputDataMem()
