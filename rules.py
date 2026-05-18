from collections import Counter
from card import Card, RANK_ORDER


FIVE_CARD_RANKING = {
    "straight": 0,
    "flush": 1,
    "full_house": 2,
    "four_of_a_kind": 3,
    "straight_flush": 4,
}


def sort_cards(cards: list[Card]) -> list[Card]:
    return sorted(cards, key=lambda card: card.sort_key())


def get_highest_card(cards: list[Card]) -> Card:
    return max(cards, key=lambda card: card.sort_key())


def is_single(cards: list[Card]) -> bool:
    return len(cards) == 1


def is_pair(cards: list[Card]) -> bool:
    return len(cards) == 2 and cards[0].rank == cards[1].rank


def is_triple(cards: list[Card]) -> bool:
    return len(cards) == 3 and len({card.rank for card in cards}) == 1


def is_flush(cards: list[Card]) -> bool:
    return len(cards) == 5 and len({card.suit for card in cards}) == 1


def is_straight(cards: list[Card]) -> bool:
    if len(cards) != 5:
        return False

    rank_values = sorted(RANK_ORDER[card.rank] for card in cards)

    # In this Big 2 rule set, straights cannot contain 2.
    if rank_values[-1] == RANK_ORDER["2"]:
        return False

    for i in range(4):
        if rank_values[i + 1] != rank_values[i] + 1:
            return False

    return True


def is_full_house(cards: list[Card]) -> bool:
    if len(cards) != 5:
        return False

    counts = sorted(Counter(card.rank for card in cards).values())
    return counts == [2, 3]


def is_four_of_a_kind(cards: list[Card]) -> bool:
    if len(cards) != 5:
        return False

    counts = sorted(Counter(card.rank for card in cards).values())
    return counts == [1, 4]


def is_straight_flush(cards: list[Card]) -> bool:
    return is_straight(cards) and is_flush(cards)


def get_play_type(cards: list[Card]) -> str | None:
    """
    Return the play type:
    - single
    - pair
    - triple
    - straight
    - flush
    - full_house
    - four_of_a_kind
    - straight_flush
    - None
    """
    cards = sort_cards(cards)

    if is_single(cards):
        return "single"
    if is_pair(cards):
        return "pair"
    if is_triple(cards):
        return "triple"
    if is_straight_flush(cards):
        return "straight_flush"
    if is_four_of_a_kind(cards):
        return "four_of_a_kind"
    if is_full_house(cards):
        return "full_house"
    if is_flush(cards):
        return "flush"
    if is_straight(cards):
        return "straight"

    return None


def compare_single(play1: list[Card], play2: list[Card]) -> int:
    """
    Compare two singles.

    Return:
    - 1 if play1 is stronger than play2
    - -1 if play1 is weaker than play2
    - 0 if they are equal
    """
    card1 = play1[0]
    card2 = play2[0]

    if card1.rank_value() > card2.rank_value():
        return 1
    if card1.rank_value() < card2.rank_value():
        return -1

    if card1.suit_value() > card2.suit_value():
        return 1
    if card1.suit_value() < card2.suit_value():
        return -1

    return 0


def get_pair_key(pair: list[Card]) -> tuple[int, int]:
    """
    Return the strength key for a pair.

    Pair comparison rule:
    1. Compare the pair rank first.
    2. If both pairs have the same rank, compare the highest suit inside the pair.

    Example:
    Q♥ Q♠ beats Q♦ Q♣ because both are Q pairs, and ♠ is higher.
    """
    sorted_pair = sort_cards(pair)
    highest_card = sorted_pair[-1]
    return highest_card.rank_value(), highest_card.suit_value()


def compare_pair(play1: list[Card], play2: list[Card]) -> int:
    key1 = get_pair_key(play1)
    key2 = get_pair_key(play2)

    if key1 > key2:
        return 1
    if key1 < key2:
        return -1

    return 0


def compare_triple(play1: list[Card], play2: list[Card]) -> int:
    rank1 = play1[0].rank_value()
    rank2 = play2[0].rank_value()

    if rank1 > rank2:
        return 1
    if rank1 < rank2:
        return -1

    return 0


def get_straight_high_card(cards: list[Card]) -> Card:
    return get_highest_card(cards)


def get_flush_key(cards: list[Card]) -> tuple[int, int]:
    """
    Flush comparison rule:
    Compare the highest card first by rank, then by suit.
    """
    highest_card = get_highest_card(cards)
    return highest_card.rank_value(), highest_card.suit_value()


def get_full_house_trip_rank(cards: list[Card]) -> int:
    counter = Counter(card.rank for card in cards)

    for rank, count in counter.items():
        if count == 3:
            return RANK_ORDER[rank]

    raise ValueError("The cards are not a full house.")


def get_four_of_a_kind_rank(cards: list[Card]) -> int:
    counter = Counter(card.rank for card in cards)

    for rank, count in counter.items():
        if count == 4:
            return RANK_ORDER[rank]

    raise ValueError("The cards are not a four of a kind.")


def compare_five_card(play1: list[Card], play2: list[Card]) -> int:
    type1 = get_play_type(play1)
    type2 = get_play_type(play2)

    if type1 not in FIVE_CARD_RANKING or type2 not in FIVE_CARD_RANKING:
        raise ValueError("compare_five_card can only compare valid five-card plays.")

    # Different five-card types are compared by hand ranking first.
    if FIVE_CARD_RANKING[type1] > FIVE_CARD_RANKING[type2]:
        return 1
    if FIVE_CARD_RANKING[type1] < FIVE_CARD_RANKING[type2]:
        return -1

    # If both plays are the same five-card type, compare their internal strength.
    if type1 in ("straight", "straight_flush"):
        card1 = get_straight_high_card(play1)
        card2 = get_straight_high_card(play2)

        if card1.rank_value() > card2.rank_value():
            return 1
        if card1.rank_value() < card2.rank_value():
            return -1
        if card1.suit_value() > card2.suit_value():
            return 1
        if card1.suit_value() < card2.suit_value():
            return -1

        return 0

    if type1 == "flush":
        key1 = get_flush_key(play1)
        key2 = get_flush_key(play2)

        if key1 > key2:
            return 1
        if key1 < key2:
            return -1

        return 0

    if type1 == "full_house":
        rank1 = get_full_house_trip_rank(play1)
        rank2 = get_full_house_trip_rank(play2)

        if rank1 > rank2:
            return 1
        if rank1 < rank2:
            return -1

        return 0

    if type1 == "four_of_a_kind":
        rank1 = get_four_of_a_kind_rank(play1)
        rank2 = get_four_of_a_kind_rank(play2)

        if rank1 > rank2:
            return 1
        if rank1 < rank2:
            return -1

        return 0

    return 0


def compare_plays(play1: list[Card], play2: list[Card]) -> int:
    """
    Compare two legal plays with the same number of cards.

    Return:
    - 1 if play1 is stronger than play2
    - -1 if play1 is weaker than play2
    - 0 if they are equal
    """
    type1 = get_play_type(play1)
    type2 = get_play_type(play2)

    if type1 is None or type2 is None:
        raise ValueError("Invalid play cannot be compared.")

    if len(play1) != len(play2):
        raise ValueError("Plays with different card counts cannot be compared directly.")

    if len(play1) == 1:
        return compare_single(play1, play2)

    if len(play1) == 2:
        if type1 != "pair" or type2 != "pair":
            raise ValueError("Two-card plays must both be pairs.")
        return compare_pair(play1, play2)

    if len(play1) == 3:
        if type1 != "triple" or type2 != "triple":
            raise ValueError("Three-card plays must both be triples.")
        return compare_triple(play1, play2)

    if len(play1) == 5:
        return compare_five_card(play1, play2)

    raise ValueError("Unsupported play size.")


def is_valid_play(selected_cards: list[Card], current_table: list[Card] | None) -> bool:
    """
    Check whether selected_cards can be played over current_table.

    selected_cards:
        The cards the player wants to play.

    current_table:
        The current table cards. None or an empty list means the player can make
        any legal opening play.
    """
    selected_type = get_play_type(selected_cards)
    if selected_type is None:
        return False

    if not current_table:
        return True

    table_type = get_play_type(current_table)
    if table_type is None:
        return False

    # A play can only beat another play with the same number of cards.
    if len(selected_cards) != len(current_table):
        return False

    # Singles, pairs, and triples must match the same play type.
    # Five-card plays can be compared across five-card types because they have
    # a ranking hierarchy.
    if len(selected_cards) in (1, 2, 3) and selected_type != table_type:
        return False

    try:
        return compare_plays(selected_cards, current_table) == 1
    except ValueError:
        return False
