class ALU_control:
    def __init__(self):
        self.ALU_CONTROL_CODES = {
            "ADD": "0010",
            "SUB": "0110",
            "AND": "0000",
            "OR": "0001",
            "XOR": "0111",
            "None": "1000",
        }

    def get_control_bits(self, type, alu_op, funct3=None, funct7=None):
        alu_control_input = self.ALU_CONTROL_CODES["None"]  # Default
        
        if alu_op == "10":  # R-type operations
            if funct3 == "000":
                if funct7 is None:
                    raise ValueError("funct7 must be specified for ADD/SUB")
                alu_control_input = (
                    self.ALU_CONTROL_CODES["ADD"]
                    if funct7 == "0000000"
                    else self.ALU_CONTROL_CODES["SUB"]
                )
            elif funct3 == "100":
                alu_control_input = self.ALU_CONTROL_CODES["XOR"]  # "XOR"
            elif funct3 == "110":
                alu_control_input = self.ALU_CONTROL_CODES["OR"]
            elif funct3 == "111":
                alu_control_input = self.ALU_CONTROL_CODES["AND"]
            else:
                raise ValueError(f"Invalid funct3 value: {funct3}")
                
        elif alu_op == "11":  # I-type operations including JAL
            if type == "I":
                print("funct3:", funct3, funct3 == "000")
                if funct3 == "000":
                    alu_control_input = self.ALU_CONTROL_CODES["ADD"]  # "ADDI"
                elif funct3 == "100":
                    alu_control_input = self.ALU_CONTROL_CODES["XOR"]  # "XORI"
                elif funct3 == "110":
                    alu_control_input = self.ALU_CONTROL_CODES["OR"]  # "ORI"
                elif funct3 == "111":
                    alu_control_input = self.ALU_CONTROL_CODES["AND"]  # "ANDI"
            elif type == "J":
                alu_control_input = self.ALU_CONTROL_CODES[
                    "ADD"
                ]  # JAL will use ADD to compute the next PC
        elif alu_op == "00":  # S-type operations (store)
            alu_control_input = self.ALU_CONTROL_CODES[
                "ADD"
            ]  # Store uses ADD for address calculation
        elif alu_op == "01":  # B-type operations (branch)
            alu_control_input = self.ALU_CONTROL_CODES[
                "SUB"
            ]  # Branches use SUB for comparison

        return alu_control_input