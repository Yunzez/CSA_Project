import os
class DataMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        self.ioDir = ioDir
        with open(os.path.join(ioDir, 'dmem.txt')) as dm:
            self.DMem = [data.replace("\n", "") for data in dm.readlines()]

    def readInstr(self, ReadAddress):
        print("reading data from: ", ReadAddress)
        if ReadAddress < 0 :
            raise ValueError("Invalid ReadAddress: Out of bounds")

        # Fetch the instruction from IMem
        data_parts = self.DMem[ReadAddress : ReadAddress + 4]
        data = "".join(data_parts)

        # Convert to integer for bitwise operations
        data_int = int(data, 2)

        data_decimal = None
        # Check if the data represents a negative number and handle accordingly
        if data[0] == '1':  # Negative number in two's complement
            # Convert to a negative number
            data_int = ~data_int & 0xFFFFFFFF  # Bitwise NOT and mask to 32 bits
            data_int += 1  # Add 1
            data_decimal = -data_int
        else:
            data_decimal = data_int

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

    def outputDataMem(self, testcase):
        output_dir = os.path.join(self.ioDir, '..', "..", 'output_yz8751', testcase)
        
        # Check if the directory exists, and if not, create it
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        res_file_path = os.path.join(output_dir, self.id + "_DMEMResult.txt")
        with open(res_file_path, "w") as rp:
            rp.writelines([str(data) + "\n" for data in self.DMem])
