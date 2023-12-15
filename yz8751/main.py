import os
import argparse

from InstructionDecoder import Decoder
from ALU import ALU
from State import State
from InstructionMem import InsMem
from DataMem import DataMem
from RegisterFile import RegisterFile
from ALU_Control import ALU_control
from BranchControlUnit import BranchControlUnit
from ForwardingUnit import ForwardingUnit

MemSize = 1000  # memory size, in reality, the memory size should be 2^32, but for this lab, for the space resaon, we keep it as this large number, but the memory is still 32-bit addressable.

class ExtoIDForwardRegister:
    def __init__(self):
        self.forward_data = None

    def set_forward_data(self, reg_addr, value):
        self.forward_data = {"reg_addr": reg_addr, "value": value}

    def get_forward_data(self, reg_addr):
        if self.forward_data and self.forward_data["reg_addr"] == reg_addr:
            return self.forward_data["value"]
        return None

    def clear(self):
        self.forward_data = None

    def toString(self):
        return str(self.forward_data)

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
        super(SingleStageCore, self).__init__(ioDir, imem, dmem, "SS_", testcase)
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
    def __init__(self, ioDir, imem, dmem, testcase):
        super(FiveStageCore, self).__init__(ioDir, imem, dmem, "FS_", testcase)
        self.opFilePath = os.path.join(ioDir, "..", "output_yz8751", testcase, "StateResult_FS.txt")
        self.Instrs = []

        # This will create a path like '/Users/yunzezhao/Code/CSA_Project/output_yz8751/PerformanceMetrics_Result.txt'

        print("start 5 stage core")
        self.alu = ALU()
        self.alu_control = ALU_control()
        self.decoder = Decoder()
        self.branchControlUnit = BranchControlUnit()
        self.forwardingUnit = ForwardingUnit()

        # ! signals for handling data hazards:
        self.alu_result = None
        self.branch_taken = False
        self.nop = False
        self.load_registers = {}

        def is_waiting_for_load(register):
            print("checking if register is waiting for load:", register, self.load_registers)
            return self.load_registers.get(register, False)

        def update_load_registers(self, instruction, is_start=True):
            if instruction and instruction["type"] == "I" and "rd" in instruction:
                self.load_registers[instruction["rd"]] = is_start
    
        self.is_waiting_for_load = is_waiting_for_load
        self.update_load_registers = update_load_registers
        self.stalled = False
        self.forwarded = False

        # we use a register to handl ex to id forward
        self.ex_to_id_forward_register = ExtoIDForwardRegister()

        # * initial all stage to be NOP (no operation)
        self.state.ID["nop"] = True
        self.state.EX["nop"] = True
        self.state.MEM["nop"] = True
        self.state.WB["nop"] = True

        self.halt_prep = False

    def step(self):
        self.halted = False # * reset halt signal
        self.forwarded = False # * reset forwarded signal
        self.nop = False
        self.nextState = State()

        # we use two forwarding signals to handle forwarding from MEM to EX and MEM to ID
        mem_to_id_forwarding = None
        mem_to_ex_forwarding = None
        print("   ")
        print("============ start of one cycle ==================" + " cycle:", self.cycle, "\n")
        print("load registers", self.load_registers)
        print("Stalled: ", self.stalled)
       
        # Your implementation
        # ! --------------------- WB stage ---------------------
        print("!----- WB -----!")
        print("WB state:", self.state.WB)

        print("WB stage :", self.state.WB["nop"])
        if self.state.WB["nop"] != True:
            if self.state.WB["wrt_enable"]:
                data = self.state.WB["Wrt_data"]
                self.myRF.writeRF(self.state.WB["Wrt_reg_addr"], data)
                print("write back:", data, "to register:", self.state.WB["Wrt_reg_addr"])
               
                # Check if this was a load instruction completing its operation
                print("cancel load register for:", self.state.WB["Wrt_reg_addr"])
                if self.load_registers.get(self.state.WB["Wrt_reg_addr"], False):
                    # Mark the load operation as completed for this register
                    self.load_registers[self.state.WB["Wrt_reg_addr"]] = False
            else:
                pass

        # ! --------------------- MEM stage --------------------

        fwType = None
        print("!----- MEM -----!")
        print("MEM state:", self.state.MEM)
        if self.state.MEM["nop"] != True:

            # * Load Instruction
            if self.state.MEM["rd_mem"]:

                # Calculate the memory address to read from
                mem_address = self.state.MEM["ALUresult"]
                # Access the memory and read the data
                read_data = self.ext_dmem.readInstr(mem_address)
                # Save the read data for the Write Back (WB) stage
                print("load type instruction, read memory from", mem_address)
                fwType = 'wrt'
                self.nextState.WB["Wrt_data"] = read_data


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
                fwType = 'str'
            else:
                self.nextState.WB["Wrt_data"] = self.state.MEM["ALUresult"]
                fwType = 'alu'

            # * update general state for next action
            # True for load (rd_mem) instructions and any R-type or I-type instructions
            # For store instructions (wrt_mem), it should be False
            self.nextState.WB["wrt_enable"] = self.state.MEM["wrt_enable"]
            self.nextState.WB["Wrt_reg_addr"] = self.state.MEM["Wrt_reg_addr"]
            self.nextState.WB["Rs"] = self.state.MEM["Rs"]
            self.nextState.WB["Rt"] = self.state.MEM["Rt"]

        # ! --------------------- EX stage ---------------------
        print("!----- EX -----!")
        print("EX state: ", self.state.EX)
        if self.state.EX["nop"] != True:

            # * forwarding MEM to EX ----
            if not self.stalled: # * here we need to wait for the stall to be resolved, or we will be fowarding to the wrong cycle
                mem_to_ex_forwarding = self.forwardingUnit.check_mem_id_forwarding(self.state.EX, self.state.MEM, self.nextState.WB, fwType)
                print("forwarding from MEM to EX:", mem_to_ex_forwarding)
                if mem_to_ex_forwarding:
                    self.state.EX.update(mem_to_ex_forwarding)
                    self.forwarded = True
                    print("forwarding, cancel load register for:", self.state.WB["Wrt_reg_addr"])
                    if fwType == 'wrt' and self.load_registers.get(self.state.MEM["Wrt_reg_addr"], False):
                        # Mark the load operation as completed for this register
                        self.load_registers[self.state.MEM["Wrt_reg_addr"]] = False
            
            # * alu operation
            alu_control_input = self.state.EX["alu_control"]
            print("alu operation:", alu_control_input, "add imm (is I type) ?", self.state.EX["is_I_type"])


            data1 = bin_to_int(self.state.EX["Read_data1"])
            data2 = bin_to_int(self.state.EX["Read_data2"] if not self.state.EX["is_I_type"] else self.state.EX["Imm"])
            print("data2: ", data2, ", ALU control: ", alu_control_input)
            self.alu_result = self.alu.operate(alu_control_input, data1, data2)

            print("alu result:", self.alu_result)

            # * we handled branch in ID

            # ! set state for next action, nextState shows up here
            # Define instruction settings
            instruction_settings = {
                "LW": {"rd_mem": 1, "wrt_mem": 0, "wrt_enable": 1, "Wrt_reg_addr": self.state.EX["Wrt_reg_addr"]},
                "I_generic": {"rd_mem": 0, "wrt_mem": 0, "wrt_enable": 1, "Wrt_reg_addr": self.state.EX["Wrt_reg_addr"]},
                "S": {"rd_mem": 0, "wrt_mem": 1, "wrt_enable": 0},
                "R": {"rd_mem": 0, "wrt_mem": 0, "wrt_enable": 1, "Wrt_reg_addr": self.state.EX["Wrt_reg_addr"]},
                "B": {"rd_mem": 0, "wrt_mem": 0, "wrt_enable": 0},
                "J": {"rd_mem": 0, "wrt_mem": 0, "wrt_enable": 1, "Wrt_reg_addr": self.state.EX["Wrt_reg_addr"]},
            }

            settings = {}
            # Apply settings based on instruction type and opcode
            if self.state.EX["is_I_type"] and self.state.EX["is_load"]:  # LW instruction
                print("lw instruction")
                settings = instruction_settings["LW"]
            elif self.state.EX["is_I_type"] and not self.state.EX["alu_op"] == "00":  # avoid store
                print("I type instruction, not S")
                settings = instruction_settings["I_generic"]
            else:
                if self.state.EX["alu_op"] == "00":
                    settings = instruction_settings["S"]
                elif self.state.EX["alu_op"] == "01":
                    settings = instruction_settings["B"]
                elif self.state.EX["alu_op"] == "10":
                    settings = instruction_settings["R"]
                else:
                    settings = instruction_settings["J"]
                    # * jump use same opcode as I type, but we filter out I-type using is_I_type signal

            print("settings:", settings)
            self.nextState.MEM.update(settings)
            print("next state mem:", self.nextState.MEM)

            # ! Handle only store data, get data from forwarding earlier in EX stage
            if self.state.EX["is_I_type"] and self.state.EX["alu_op"] == "00":  # store instruction
                store_data = None
                if mem_to_ex_forwarding and "Read_data2" in mem_to_ex_forwarding:  # Check if data is forwarded
                    store_data = mem_to_ex_forwarding["Read_data2"]
                else:
                    store_data = self.myRF.readRF(self.state.EX["Rt"])  # Read from register file

                self.nextState.MEM["Store_data"] = store_data
                print("hanld mem to ex forward", mem_to_ex_forwarding)
                print("store data in next stage:", self.nextState.MEM["Store_data"])

            # Always set these values
            self.nextState.MEM["ALUresult"] = self.alu_result
            self.nextState.MEM["Rs"] = self.state.EX["Rs"]
            self.nextState.MEM["Rt"] = self.state.EX["Rt"]


            # * EX to ID forwarding ----
            if not self.nextState.MEM["wrt_enable"]:
                self.ex_to_id_forward_register.set_forward_data(self.state.EX["Wrt_reg_addr"], self.alu_result)
                print("push ex to id forwarding cuz wrt_enable in next state:", self.ex_to_id_forward_register.toString())


            # ! suspecting
            if self.state.EX["alu_op"] == "10":
                self.ex_to_id_forward_register.set_forward_data(self.state.EX["Wrt_reg_addr"], self.alu_result)
                print("push ex to id forwarding cuz alu op is R type:", self.ex_to_id_forward_register.toString())
      
        # ! --------------------- ID stage ---------------------
        print("!----- ID -----!")
        print("ID state:", self.state.ID)

        if self.state.ID["nop"] != True and self.state.ID["Instr"] != None:
            
            print("ID stage instruction:", self.state.ID["Instr"])
            decodeResult = Decoder().decode(self.state.ID["Instr"])
            print("decode result:", decodeResult)

            # * forwarding MEM to ID ----
            if not self.stalled: # * here we need to wait for the stall to be resolved, or we will be fowarding to the wrong cycle
                mem_to_id_forwarding = self.forwardingUnit.check_mem_id_forwarding(decodeResult, self.state.MEM, self.nextState.WB, fwType)
                print("forwarding from MEM to ID:", mem_to_id_forwarding)
                if mem_to_id_forwarding:
                    self.state.EX.update(mem_to_id_forwarding)
                    # self.forwarded = True
                    print("forwarding, cancel load register for:", self.state.WB["Wrt_reg_addr"])
                    if fwType == 'wrt' and self.load_registers.get(self.state.MEM["Wrt_reg_addr"], False):
                        # Mark the load operation as completed for this register
                        self.load_registers[self.state.MEM["Wrt_reg_addr"]] = False
          
            # ! ----- detect_load_use_hazard -----
            if self.stalled:
                self.stalled = False
             # Get the current instruction in the ID stage
            current_id_instr = self.state.ID["Instr"]
            decode_result = self.decoder.decode(current_id_instr)

            # Check if the current instruction is dependent on a preceding LW instruction
            if decode_result["type"] not in ["NOP", "HALT"]:
                rs1 = decode_result.get("rs1")
                rs2 = decode_result.get("rs2")

                # Check if rs1 or rs2 are waiting for data from a LW instruction
                if  (self.is_waiting_for_load(rs1) or self.is_waiting_for_load(rs2)):
                    print("ID stage stalled due to load-use hazard")
                    self.stalled = True
                    # return 

                if decodeResult["type"] == "I":  # Assuming LW opcode is "0000011"
                    print("lw instruction, add to load registers")
                    self.load_registers[decodeResult["rd"]] = True

            

            # halt on halt instruction
            if decodeResult["type"] == "HALT":
                print("halted")
                self.nextState.IF["nop"] = True
                self.nextState.ID["nop"] = True
                self.nextState.EX["nop"] = True
                # * we set EX to nop because next cycle EX will run
                self.halt_prep = True

            if decodeResult["type"] == "NOP":
                print("nop")
                self.nop = True

            # Set ALU operation based on type
            alu_ops = {"R": "10", "I": "11", "S": "00", "B": "01", "J": "11"}
            self.nextState.EX["alu_op"] = alu_ops.get(decodeResult["type"], "")

            # Common operations
            rs1 = self.myRF.readRF(decodeResult["rs1"]) if "rs1" in decodeResult else None
            imm = decodeResult["Imm"] if "Imm" in decodeResult else 0
            self.nextState.EX["Rs"] = decodeResult.get("rs1", None)
            self.nextState.EX["Read_data1"] = rs1
            self.nextState.EX["is_I_type"] = False
            self.nextState.EX["Imm"] = imm

            if "rs2" in decodeResult:
                self.nextState.EX["Rt"] = decodeResult["rs2"]

            if "rd" in decodeResult:
                self.nextState.EX["Wrt_reg_addr"] = decodeResult["rd"]
            # type specific
            if decodeResult["type"] == "I":
                if decodeResult["opcode"] == "0000011":  # LW instruction
                    self.nextState.EX["is_load"] = True

                self.nextState.EX["is_I_type"] = True  # overwrite

            if decodeResult["type"] == "R":
                self.nextState.EX["Read_data2"] = self.myRF.readRF(decodeResult["rs2"])

            if decodeResult["type"] == "S":
                self.nextState.EX["is_I_type"] = True  # ! we need this to be true so imm is used instead of Read_data2, I treat this as a use imm signal

            if decodeResult["type"] == "B":
                 self.nextState.EX["Read_data2"] = rs2

            if decodeResult["type"] == "J":
                # this will be PC + 4
                self.nextState.EX["Read_data1"] = self.state.IF["PC"]
                self.nextState.EX["Read_data2"] = 4
                print("j type data:", self.nextState.EX["Read_data1"], self.nextState.EX["Read_data2"])
                print("jump to address:", self.state.IF["PC"], " + ", bin_to_int(imm))
                self.state.IF["PC"] = self.state.IF["PC"] + bin_to_int(imm)

            alu_control_input = self.alu_control.get_control_bits(
                decodeResult["type"], self.nextState.EX["alu_op"], decodeResult["funct3"] if "funct3" in decodeResult else None, decodeResult["funct7"] if "funct7" in decodeResult else None
            )

            self.nextState.EX["alu_control"] = alu_control_input
            print("alu operation:", alu_control_input, "add imm ?", self.nextState.EX["is_I_type"])


            # * get data for EX to ID forwarding
            forwarded_data1 = self.ex_to_id_forward_register.get_forward_data(decodeResult.get("rs1"))
            forwarded_data2 = self.ex_to_id_forward_register.get_forward_data(decodeResult.get("rs2"))
            print("forwarded data:", forwarded_data1, forwarded_data2)

            # Update Read_data1 and Read_data2 with forwarded data if necessary
            if forwarded_data1 is not None and "rs1" in decodeResult:
                self.nextState.EX["Read_data1"] = forwarded_data1

            if forwarded_data2 is not None and "rs2" in decodeResult:
                self.nextState.EX["Read_data2"] = forwarded_data2


            # * get data from MEM to ID forwarding
            if mem_to_id_forwarding:
                print("forwarding from MEM to ID:", mem_to_id_forwarding)
                self.nextState.EX.update(mem_to_id_forwarding)

            # * we handle branch at last as we will need forwarding information 
            if decodeResult["type"] == "B" and not self.stalled:
                # ! handle branch in the BranchControlUnit
                # * Ex to Id forwarding
                if forwarded_data2 is not None :
                    rs2 = forwarded_data2
                else: 
                    rs2 = self.myRF.readRF(decodeResult["rs2"])
                
                if forwarded_data1 is not None:
                    rs1 = forwarded_data1
                
                # * MEM to Id forwarding
                if mem_to_id_forwarding:
                    if "Read_data2" in mem_to_id_forwarding:
                        rs2 = mem_to_id_forwarding["Read_data2"]
                    if "Read_data1" in mem_to_id_forwarding:
                        rs1 = mem_to_id_forwarding["Read_data1"]
                
                branch_taken, branch_target = self.branchControlUnit.evaluateBranch(decodeResult, rs1, rs2, self.state.IF["PC"] - 4, bin_to_int(imm))

                print("branch taken:", branch_taken, "branch target:", branch_target)
                if branch_taken:
                    self.branch_taken = True
                    # Update PC for branch or jump
                    self.state.IF["PC"] = branch_target

                    # Set NOP for subsequent stages
                    self.nextState.EX["nop"] = True

                else:
                    if  decodeResult["type"] != "NOP":
                        self.nextState.EX["nop"] = False  

                    self.nextState.MEM["nop"] = False
                    self.nextState.WB["nop"] = False
                    print("branch not taken")
                    # Normal instruction, increment PC by 4, we already did this in the IF stage

        # ! --------------------- IF stage ---------------------
        print("!----- IF -----!")
        print("IF state:", self.state.IF)
        print("IF stage nop: ", self.state.IF["nop"])

        if  self.stalled == True:
            print("stalled, skip IF")
            self.nextState.EX["nop"] = True
            self.nextState.ID["nop"] = self.state.IF["nop"]
            self.nextState.ID["Instr"] = self.state.ID["Instr"]
            self.nextState.IF["PC"] = self.state.IF["PC"]

        elif self.state.IF["nop"]:
            self.nextState.WB["nop"] = self.state.MEM["nop"]
            self.nextState.MEM["nop"] = self.state.EX["nop"]
            self.nextState.EX["nop"] = self.state.ID["nop"]
            self.nextState.ID["nop"] = self.state.IF["nop"]
            self.nextState.IF["nop"] = True

        elif self.halt_prep == False:
            current_instruction = self.ext_imem.readInstr(self.state.IF["PC"])
            print("IF stage instruction:", current_instruction)

            self.nextState.ID["Instr"] = current_instruction

            self.nextState.IF["PC"] = self.state.IF["PC"] + 4
            self.nextState.ID["PC"] = self.nextState.IF["PC"]

            self.nextState.EX["nop"] = self.state.ID["nop"]
            self.nextState.ID["nop"] = self.state.IF["nop"]
            self.nextState.IF["nop"] = self.state.IF["nop"]

            if self.nop:
                print("nop in EX, trigger NOP cycle")
                self.nextState.EX["nop"] = True

            
            if current_instruction not in self.Instrs:
                self.Instrs.append(current_instruction)

            print(
                "pc:",
                self.state.IF["PC"],
                current_instruction,
            )
        
       
       

        if self.state.IF["nop"] and self.state.ID["nop"] and self.state.EX["nop"] and self.state.MEM["nop"] and self.state.WB["nop"]:
            self.halted = True

        

        # ! ending of one cycle
        self.myRF.outputRF(self.cycle)  # dump RF
        self.printState(self.nextState, self.cycle)  # print states after executing cycle 0, cycle 1, cycle 2 ...

        self.state = self.nextState  # The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1

        # # ! testing only
        # if self.cycle > 15: 
        #     self.halted = True

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
    imem_path = os.path.join(path, "imem.txt")
    dmem_path = os.path.join(path, "dmem.txt")
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
    input_dir = os.path.join(script_dir, "..", "input")
    output_dir = os.path.join(script_dir, "..", "output_yz8751")
    # ! Prompt user for testcase
    testcase_path = None
    while True:
        testcase = input("Enter the name of the testcase you wish to use, testcase should be folder under the input folder: ")
        testcase_path = os.path.join(input_dir, testcase)
        print("testcase path", testcase_path)
        if is_valid_testcase(testcase_path):
            print(f"Using testcase: {testcase}")
            print("testcase path:", testcase_path)
            break
        else:
            print(f"Testcase {testcase} is invalid or does not contain imem.txt and dmem.txt.")

    imem = InsMem("Imem", testcase_path)
    dmem_ss = DataMem("SS", testcase_path)
    dmem_fs = DataMem("FS", testcase_path)

    ssCore = SingleStageCore(script_dir, imem, dmem_ss, testcase)

    # ! open the five step core later
    fsCore = FiveStageCore(script_dir, imem, dmem_fs, testcase)

    while True:
        if not ssCore.halted:
            ssCore.step()

        # ! open the five step core later
        if not fsCore.halted:
            print("step")
            fsCore.step()

        # ! change to and statement later
        if ssCore.halted and fsCore.halted:
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
        f.write(f"Number of cycles taken: {fsCore.cycle}\n")
        f.write(f"Cycles per instruction: {round(fsCore.cycle/len(fsCore.Instrs) ,5)}\n")
        f.write(f"Instructions per cycle: {round(len(fsCore.Instrs)/fsCore.cycle , 6)}\n")


