from dataclasses import dataclass

RANK_ORDER = {
    "3": 0, "4": 1, "5": 2, "6": 3, "7": 4,
    "8": 5, "9": 6, "10": 7, "J": 8, "Q": 9,
    "K": 10, "A": 11, "2": 12
}

# Suit order: diamonds < clubs < hearts < spades
SUIT_ORDER = {
    "♦": 0,
    "♣": 1,
    "♥": 2,
    "♠": 3
}


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str

    def rank_value(self) -> int:
        return RANK_ORDER[self.rank]

    def suit_value(self) -> int:
        return SUIT_ORDER[self.suit]

    def sort_key(self):
        return (self.rank_value(), self.suit_value())

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"

    def __repr__(self) -> str:
        return str(self)