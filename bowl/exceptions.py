__all__ = ["MessageSupplyException", "ShouldNeverHappen"]

class MessageSupplyException(Exception):
    pass

class ShouldNeverHappen(Exception):

    def __init__(self, number: int) -> None:
        message = (f"SNV{number:05} - please contact @Garmy with the code on"
                " the left if you see this")
        super().__init__(message)
