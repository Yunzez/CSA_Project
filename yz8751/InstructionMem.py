class InsMem(object):
    def __init__(self, name, ioDir):
        self.id = name

        with open(ioDir + "/input/testcase3/imem.txt") as im:
            self.IMem = [data.replace("\n", "") for data in im.readlines()]

    def readInstr(self, ReadAddress):
        print("reading instructions from: ", ReadAddress)
        # Check if the ReadAddress is within bounds
        print("instruction count:", len(self.IMem) // 4)
        if ReadAddress < 0 or ReadAddress >= len(self.IMem):
            raise ValueError("Invalid ReadAddress: Out of bounds")

        # Fetch the instruction from IMem
        instruction_parts = self.IMem[ReadAddress : ReadAddress + 4]
        instruction = "".join(instruction_parts)

        # Convert to 32-bit hex (if not already)
        instruction_hex = format(
            int(instruction, 2), "08x"
        )  # Assuming instruction is a hex string without '0x'

        print("reading instructions from:", ReadAddress, "Value:", instruction)
        return instruction_hex