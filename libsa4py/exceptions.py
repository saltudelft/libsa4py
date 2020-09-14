class ParseError(Exception):
    def __init__(self, msg: str):
        super().__init__("ParseError: " + msg)


class OutputSequenceException(Exception):
    """
    An exception for malformed output sequences that are not aligned properly with their input sequences
    """

    def __init__(self, in_seq: str, out_seq: str):
        super().__init__("Malformed output sequence: " + in_seq + " -> " + out_seq)
