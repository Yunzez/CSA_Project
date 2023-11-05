class RegisterFile(object):
    def __init__(self, ioDir):
        self.outputFile = ioDir + "RFResult.txt"
        self.Registers = [0x0 for i in range(32)]

    def readRF(self, Reg_addr):
        decimal = int(Reg_addr, 2)
        print("reading register from:", decimal)
        return self.Registers[int(decimal)]

    def writeRF(self, Reg_addr, Wrt_reg_data):
        print("write rf: ", Reg_addr, "decimal: ", int(Reg_addr, 2),  " with data:", Wrt_reg_data)
        decimal = int(Reg_addr, 2)
        self.Registers[decimal] = Wrt_reg_data

    def outputRF(self, cycle):
        op = ["-" * 70 + "\n", "State of RF after executing cycle:" + str(cycle) + "\n"]
        op.extend([str(val) + "\n" for val in self.Registers])
        if cycle == 0:
            perm = "w"
        else:
            perm = "a"
        with open(self.outputFile, perm) as file:
            file.writelines(op)
