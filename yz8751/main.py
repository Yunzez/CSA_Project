import os
import argparse

from InstructionDecoder import Decoder
from ALU import ALU
from State import State
from InstructionMem import InsMem
from DataMem import DataMem
from RegisterFile import RegisterFile
from ALU_Control import ALU_control

MemSize = 1000  # memory size, in reality, the memory size should be 2^32, but for this lab, for the space resaon, we keep it as this large number, but the memory is still 32-bit addressable.


def bin_to_int(value):
    if isinstance(value, int):
        return value

    # Ensure the value is a string from this point onwards
    binary_str = str(value)

    # Check if the number is negative (MSB is 1)
    if binary_str[0] == "1":
        # Compute negative number
        return -((int(binary_str, 2) ^ ((1 << len(binary_str)) - 1)) + 1)
    else:
        # Number is positive, so just convert to int
        return int(binary_str, 2)


class Core(object):
    def __init__(self, ioDir, imem, dmem, prefix=""):
        self.myRF = RegisterFile(ioDir, prefix)
        self.cycle = 0
        self.halted = False
        self.ioDir = ioDir
        self.state = State()
        self.nextState = State()
        self.ext_imem = imem
        self.ext_dmem = dmem


class SingleStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(SingleStageCore, self).__init__(ioDir, imem, dmem, "SS_")
        self.opFilePath = os.path.join(ioDir, "output_yz8751", "StateResult_SS.txt")
        self.Instrs = []

        # This will create a path like '/Users/yunzezhao/Code/CSA_Project/output_yz8751/PerformanceMetrics_Result.txt'

        print("single stage core location:", self.opFilePath)
        print("start single stage core")
        self.alu = ALU()
        self.alu_control = ALU_control()
        self.decoder = Decoder()

    def step(self):
        print("single core steps forward")
        # * 1. Instruction Fetch (IF)
        current_instruction = self.ext_imem.readInstr(self.state.IF["PC"])
        if current_instruction not in self.Instrs:
            self.Instrs.append(current_instruction)
        print(
            "current pc:",
            self.state.IF["PC"],
            "current instruction:",
            current_instruction,
        )
        # * 2. Instruction Decode (ID)
        decodeResult = Decoder().decode(current_instruction)
        print("decode result:", decodeResult)
        self.state.ID["Instr"] = current_instruction

        if decodeResult["type"] == "HALT" or decodeResult["type"] == "NOP":
            self.halted = True
            return

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
            self.state.EX["alu_op"] = "11"  # Reusing '11' for J-type, but will need special handling

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
            self.state.EX["is_I_type"] = True  # ! we need this to be true so imm is used instead of Read_data2

        if decodeResult["type"] == "J":
            self.state.EX["Imm"] = decodeResult["Imm"]
            self.state.EX["Wrt_reg_addr"] = decodeResult["rd"]
            # this will be PC + 4
            self.state.EX["Read_data1"] = self.state.IF["PC"]
            self.state.EX["Read_data2"] = 4
            print("j type data:", self.state.EX["Read_data1"], self.state.EX["Read_data2"])

        # * 3. Execute (EX)
        # * types include S I B J R

        alu_control_input = self.alu_control.get_control_bits(
            decodeResult["type"], self.state.EX["alu_op"], decodeResult["funct3"] if "funct3" in decodeResult else None, decodeResult["funct7"] if "funct7" in decodeResult else None
        )
        print("alu operation:", alu_control_input, "add imm ?", self.state.EX["is_I_type"])

        alu_result = None
        data1 = bin_to_int(self.state.EX["Read_data1"])
        data2 = bin_to_int(self.state.EX["Read_data2"] if not self.state.EX["is_I_type"] else self.state.EX["Imm"])
        alu_result = self.alu.operate(alu_control_input, data1, data2)

        print("alu result:", alu_result)

        # ! Execute branch instructions
        if decodeResult["type"] == "B":
            if (decodeResult["funct3"] == "000" and alu_result == 0) or (decodeResult["funct3"] == "001" and alu_result != 0):
                self.nextState.IF["PC"] += bin_to_int(self.state.EX["Imm"])
                if decodeResult["funct3"] == "000":
                    print("BEQ branch taken")
                if decodeResult["funct3"] == "001":
                    print("BNE branch taken")
            else:
                self.nextState.IF["PC"] += 4
        elif decodeResult["type"] == "J":
            print("j type imm:", self.state.EX["Imm"], bin_to_int(self.state.EX["Imm"]))
            self.nextState.IF["PC"] = self.state.IF["PC"] + bin_to_int(self.state.EX["Imm"])
            print("j type next pc:", self.nextState.IF["PC"])
        else:
            self.nextState.IF["PC"] += 4

        # ! set state for next action

        # Define instruction settings
        instruction_settings = {
            "LW": {"rd_mem": 1, "wrt_mem": 0, "wrt_enable": 1, "Wrt_reg_addr": self.state.EX["Wrt_reg_addr"]},
            "I_generic": {"rd_mem": 0, "wrt_mem": 0, "wrt_enable": 1, "Wrt_reg_addr": self.state.EX["Wrt_reg_addr"]},
            "S": {"rd_mem": 0, "wrt_mem": 1, "wrt_enable": 0},
            "R": {"rd_mem": 0, "wrt_mem": 0, "wrt_enable": 1, "Wrt_reg_addr": self.state.EX["Wrt_reg_addr"]},
            "B": {"rd_mem": 0, "wrt_mem": 0, "wrt_enable": 0},
            "J": {"rd_mem": 0, "wrt_mem": 0, "wrt_enable": 1, "Wrt_reg_addr": self.state.EX["Wrt_reg_addr"]},
        }

        # Apply settings based on instruction type and opcode
        if decodeResult["type"] == "I" and decodeResult["opcode"] == "0000011":  # LW instruction
            settings = instruction_settings["LW"]
        elif decodeResult["type"] == "I":
            settings = instruction_settings["I_generic"]
        else:
            settings = instruction_settings.get(decodeResult["type"], {})

        self.state.MEM.update(settings)

        # Handle store data
        if decodeResult["type"] == "S" and decodeResult["opcode"] == "0100011":
            self.state.MEM["Store_data"] = self.myRF.readRF(decodeResult["rs2"])
            print("store data:", self.state.MEM["Store_data"])

        # Always set these values
        self.state.MEM["ALUresult"] = alu_result
        self.state.MEM["Rs"] = self.state.EX["Rs"]
        self.state.MEM["Rt"] = self.state.EX["Rt"]

        # * 4. Memory Access (MEM)
        # Load Instruction
        if self.state.MEM["rd_mem"]:
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

        self.state.WB["Wrt_reg_addr"] = self.state.MEM["Wrt_reg_addr"]
        self.state.WB["Rs"] = self.state.MEM["Rs"]
        self.state.WB["Rt"] = self.state.MEM["Rt"]

        # * 5. Write Back (WB)
        if self.state.WB["wrt_enable"]:
            data = self.state.WB["Wrt_data"]
            self.myRF.writeRF(self.state.WB["Wrt_reg_addr"], data)
        else:
            pass

        self.myRF.outputRF(self.cycle)  # dump RF
        self.printState(self.nextState, self.cycle)  # print states after executing cycle 0, cycle 1, cycle 2 ...
        self.state = self.nextState  # The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = [
            "-" * 70 + "\n",
            "State after executing cycle: " + str(cycle) + "\n",
        ]
        printstate.append("IF.PC: " + str(state.IF["PC"]) + "\n")
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")

        if cycle == 0:
            perm = "w"
        else:
            perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)


class FiveStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(FiveStageCore, self).__init__(ioDir, imem, dmem, "FS_")
        self.opFilePath = ioDir + "\\StateResult_FS.txt"

    def step(self):
        # Your implementation
        # --------------------- WB stage ---------------------

        # --------------------- MEM stage --------------------

        # --------------------- EX stage ---------------------

        # --------------------- ID stage ---------------------

        # --------------------- IF stage ---------------------

        self.halted = True
        if self.state.IF["nop"] and self.state.ID["nop"] and self.state.EX["nop"] and self.state.MEM["nop"] and self.state.WB["nop"]:
            self.halted = True

        self.myRF.outputRF(self.cycle)  # dump RF
        self.printState(self.nextState, self.cycle)  # print states after executing cycle 0, cycle 1, cycle 2 ...

        self.state = self.nextState  # The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = [
            "-" * 70 + "\n",
            "State after executing cycle: " + str(cycle) + "\n",
        ]
        printstate.extend(["IF." + key + ": " + str(val) + "\n" for key, val in state.IF.items()])
        printstate.extend(["ID." + key + ": " + str(val) + "\n" for key, val in state.ID.items()])
        printstate.extend(["EX." + key + ": " + str(val) + "\n" for key, val in state.EX.items()])
        printstate.extend(["MEM." + key + ": " + str(val) + "\n" for key, val in state.MEM.items()])
        printstate.extend(["WB." + key + ": " + str(val) + "\n" for key, val in state.WB.items()])

        if cycle == 0:
            perm = "w"
        else:
            perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)


if __name__ == "__main__":
    # parse arguments for input file location
    parser = argparse.ArgumentParser(description="RV32I processor")
    parser.add_argument("--iodir", default="", type=str, help="Directory containing the input files.")
    args = parser.parse_args()

    ioDir = os.path.abspath(args.iodir)
    print("IO Directory:", ioDir)

    imem = InsMem("Imem", ioDir)
    dmem_ss = DataMem("SS", ioDir)
    dmem_fs = DataMem("FS", ioDir)

    ssCore = SingleStageCore(ioDir, imem, dmem_ss)

    # ! open the five step core later
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

    with open(os.path.join(ioDir, "output_yz8751", "PerformanceMetrics_Result.txt"), "w") as f:
        print("write performance metrics to", f.name)
        f.write(f"IO Directory: {f.name}\n")
        f.write(f"Single Stage Core Performance Metrics-----------------------------\n")
        f.write(f"Number of cycles taken: {ssCore.cycle}\n")
        f.write(f"Cycles per instruction: {round(ssCore.cycle / len(ssCore.Instrs), 5)}\n")
        f.write(f"Instructions per cycle: {round( len(ssCore.Instrs) / ssCore.cycle, 6)}\n")

        f.write(f"Five Stage Core Performance Metrics-----------------------------\n")
        # f.write(f'Number of cycles taken: {fsCore.cycle}\n')
        # f.write(f'Cycles per instruction: {round(fsCore.cycle/len(fsCore.Instrs) ,5)}\n' )
        # f.write(f'Instructions per cycle: {round(len(fsCore.Instrs)/fsCore.cycle , 6)}\n')
