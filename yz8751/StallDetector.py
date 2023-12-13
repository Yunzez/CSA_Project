class StallDetector:
    def __init__(self):
        # Dictionary to keep track of registers currently in use
        self.registers_in_use = {}

    def is_stall_needed(self, instruction):
        """
        Check if a stall is needed based on the current instruction's register usage.
        :param instruction: The instruction being decoded.
        :return: True if a stall is needed, False otherwise.
        """
        for reg in instruction.get_source_registers():
            if self.registers_in_use.get(reg, False):
                return True  # Stall is needed
        return False

    def mark_registers(self, instruction):
        """
        Mark the destination register of the instruction as in use.
        :param instruction: The instruction being processed.
        """
        if instruction.destination_register:
            self.registers_in_use[instruction.destination_register] = True

    def release_registers(self, instruction):
        """
        Release the destination register of the instruction from being in use.
        :param instruction: The instruction that has completed execution.
        """
        if instruction.destination_register:
            self.registers_in_use[instruction.destination_register] = False
