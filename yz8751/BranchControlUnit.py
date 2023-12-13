class BranchControlUnit:
    def __init__(self):
        pass

    def evaluateBranch(self, decodeResult, readData1, readData2, currentPC, imm):
        if decodeResult["type"] == "B":
            branch_taken, branch_target = self.evaluateBranchCondition(decodeResult["funct3"], readData1, readData2, currentPC, imm)
            return branch_taken, branch_target
        elif decodeResult["type"] == "J":
            # For jump instructions, the branch is always taken
            return True, currentPC + imm
        else:
            # Not a branch or jump instruction
            return False, None

    def evaluateBranchCondition(self, funct3, data1, data2, currentPC, imm):
        # BEQ and BNE conditions
        print("funct3:", funct3, "data1:", data1, "data2:", data2, "imm:", imm)
        if funct3 == "000" and data1 == data2:  # ! BEQ
            return True, currentPC + imm
        elif funct3 == "001" and data1 != data2:  # BNE
            return True, currentPC + imm
        # ... other branch conditions
        return False, currentPC + 4
