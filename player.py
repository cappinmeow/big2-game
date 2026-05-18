from typing import List
from card import Card


class Player:
    def __init__(self, name: str, is_human: bool = False):
        self.name = name
        self.hand: List[Card] = []
        self.total_score = 0
        self.is_human = is_human

    def receive_cards(self, cards: List[Card]):
        self.hand.extend(cards)
        self.sort_hand()

    def sort_hand(self):
        self.hand.sort(key=lambda card: card.sort_key())

    def remove_cards(self, cards_to_remove: List[Card]):
        for card in cards_to_remove:
            if card in self.hand:
                self.hand.remove(card)
            else:
                raise ValueError(f"{self.name} does not have {card} in hand.")
        self.sort_hand()

    def has_no_cards(self) -> bool:
        return len(self.hand) == 0

    def hand_size(self) -> int:
        return len(self.hand)

    def has_card(self, target: Card) -> bool:
        return target in self.hand

    def show_hand(self) -> str:
        return " ".join(str(card) for card in self.hand)

    def __str__(self):
        return f"{self.name} (score: {self.total_score}, cards: {len(self.hand)})"