class DataMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        self.ioDir = ioDir
        with open(ioDir + "/input/testcase1/dmem.txt") as dm:
            self.DMem = [data.replace("\n", "") for data in dm.readlines()]

    def readInstr(self, ReadAddress):
        print("reading data from: ", ReadAddress)
        if ReadAddress < 0 :
            raise ValueError("Invalid ReadAddress: Out of bounds")

        # Fetch the instruction from IMem
        data_parts = self.DMem[ReadAddress : ReadAddress + 4]
        data = "".join(data_parts)
        print('data_parts', data)
        # Convert to 32-bit hex (if not already)
        data_decimal = int(data, 2) # Assuming instruction is a hex string without '0x'

        print("reading data from:", ReadAddress, "data:", data_decimal)
        return data_decimal

    def writeDataMem(self, Address, WriteData):
        WriteData = f"{WriteData:032b}"

        print("writing data to:", Address, "data:", WriteData)

        while Address + 4 > len(self.DMem):
            self.DMem.append('0'*8)
        
        for i in range(4):
            self.DMem[Address + i] = WriteData[i*8:(i+1)*8]
        # write data into byte addressable memory

    def outputDataMem(self):
        resPath = self.ioDir + "/" + self.id + "_DMEMResult.txt"
        with open(resPath, "w") as rp:
            rp.writelines([str(data) + "\n" for data in self.DMem])
