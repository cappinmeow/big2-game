import random
from card import Card

RANKS = ["3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A", "2"]
SUITS = ["♦", "♣", "♥", "♠"]


class Deck:
    def __init__(self):
        self.cards = [Card(rank, suit) for rank in RANKS for suit in SUITS]

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, num_players=4, cards_each=13):
        if num_players * cards_each > len(self.cards):
            raise ValueError("Not enough cards to deal.")

        hands = []
        for _ in range(num_players):
            hand = []
            for _ in range(cards_each):
                hand.append(self.cards.pop())
            hands.append(hand)

        remaining_deck = self.cards[:]
        return hands, remaining_deck