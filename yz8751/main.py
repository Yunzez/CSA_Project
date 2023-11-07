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
    def __init__(self, ioDir, imem, dmem, prefix="", testcase=""):
        self.myRF = RegisterFile(ioDir, prefix, testcase)
        self.cycle = 0
        self.halted = False
        self.ioDir = ioDir
        self.state = State()
        self.nextState = State()
        self.ext_imem = imem
        self.ext_dmem = dmem


class SingleStageCore(Core):
    def __init__(self, ioDir, imem, dmem, testcase):
        super(SingleStageCore, self).__init__(ioDir, imem, dmem, "SS_" ,testcase)
        self.opFilePath = os.path.join(ioDir, "..", "output_yz8751", testcase, "StateResult_SS.txt")
        self.Instrs = []

        # This will create a path like '/Users/yunzezhao/Code/CSA_Project/output_yz8751/PerformanceMetrics_Result.txt'

        print("single stage core output location:", self.opFilePath)
        print("start single stage core")
        self.alu = ALU()
        self.alu_control = ALU_control()
        self.decoder = Decoder()

    def step(self):
        # * 1. Instruction Fetch (IF)
        current_instruction = self.ext_imem.readInstr(self.state.IF["PC"])
        if current_instruction not in self.Instrs:
            self.Instrs.append(current_instruction)
        print(
            "pc:",
            self.state.IF["PC"],
            current_instruction,
        )
        # * 2. Instruction Decode (ID)
        decodeResult = Decoder().decode(current_instruction)
        print("decode result:", decodeResult)
        self.state.ID["Instr"] = current_instruction

        # Early exit if HALT or NOP
        if decodeResult["type"] == "HALT" or decodeResult["type"] == "NOP":
            self.halted = True
            return

        # Set ALU operation based on type
        alu_ops = {"R": "10", "I": "11", "S": "00", "B": "01", "J": "11"}
        self.state.EX["alu_op"] = alu_ops.get(decodeResult["type"], "")
        # Common operations
        self.state.EX["Rs"] = decodeResult.get("rs1", None)
        self.state.EX["Read_data1"] = self.myRF.readRF(decodeResult["rs1"]) if "rs1" in decodeResult else None
        self.state.EX["is_I_type"] = False

        if "Imm" in decodeResult:
            self.state.EX["Imm"] = decodeResult["Imm"]

        if "rs2" in decodeResult:
            self.state.EX["Rt"] = decodeResult["rs2"]

        if "rd" in decodeResult:
            self.state.EX["Wrt_reg_addr"] = decodeResult["rd"]
        # type specific
        if decodeResult["type"] == "I":
            self.state.EX["is_I_type"] = True  # overwrite

        if decodeResult["type"] == "R":
            self.state.EX["Read_data2"] = self.myRF.readRF(decodeResult["rs2"])

        if decodeResult["type"] == "B":
            self.state.EX["Read_data2"] = self.myRF.readRF(decodeResult["rs2"])

        if decodeResult["type"] == "S":
            self.state.EX["is_I_type"] = True  # ! we need this to be true so imm is used instead of Read_data2

        if decodeResult["type"] == "J":
            # this will be PC + 4
            self.state.EX["Read_data1"] = self.state.IF["PC"]
            self.state.EX["Read_data2"] = 4
            print("j type data:", self.state.EX["Read_data1"], self.state.EX["Read_data2"])

        # * 3. Execute (EX)
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
                "store:",
                store_data,
                " address:",
                mem_address,
                int(mem_address, 2),
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


def is_valid_testcase(path):
    imem_path = os.path.join(path, 'imem.txt')
    dmem_path = os.path.join(path, 'dmem.txt')
    return os.path.isfile(imem_path) and os.path.isfile(dmem_path)

if __name__ == "__main__":
    # parse arguments for input file location
    parser = argparse.ArgumentParser(description="RV32I processor")
    parser.add_argument("--iodir", default="", type=str, help="Directory containing the input files.")
    
    args = parser.parse_args()

    ioDir = os.path.abspath(args.iodir)
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.realpath(__file__))
    # Path to the 'input' directory in the parent folder of the script
    input_dir = os.path.join(script_dir, '..', 'input')
    output_dir = os.path.join(script_dir, '..', 'output_yz8751')
    # ! Prompt user for testcase
    testcase_path = None
    while True:
        testcase = input("Enter the name of the testcase you wish to use, testcase should be folder under the input folder: ")
        testcase_path = os.path.join(input_dir, testcase)
        print('testcase path', testcase_path)
        if is_valid_testcase(testcase_path):
            print(f"Using testcase: {testcase}")
            print('testcase path:', testcase_path)
            break
        else:
            print(f"Testcase {testcase} is invalid or does not contain imem.txt and dmem.txt.")


    imem = InsMem("Imem", testcase_path)
    dmem_ss = DataMem("SS", testcase_path)
    dmem_fs = DataMem("FS", testcase_path)

    ssCore = SingleStageCore(script_dir, imem, dmem_ss,testcase)

    # ! open the five step core later
    fsCore = FiveStageCore(script_dir, imem, dmem_fs)

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
    dmem_ss.outputDataMem(testcase)
    dmem_fs.outputDataMem(testcase)
    print("IO Directory:", ioDir)
    with open(os.path.join(output_dir, testcase, "PerformanceMetrics_Result.txt"), "w") as f:
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
