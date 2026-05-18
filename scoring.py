from card import Card


LOW_RANKS = {"3", "4", "5", "6", "7", "8", "9"}
HIGH_RANKS = {"10", "J", "Q", "K", "A"}


def calculate_score(hand: list[Card]) -> int:
    """
    Calculate the penalty points a player receives at the end of a round.

    Rules:
    - 3 to 9: 1 point each.
    - 10/J/Q/K/A: 2 points each.
    - 2 does not add direct points, but any remaining 2 doubles the final score.
    - If more than 10 cards remain, use card_count * 2 as the base score.
    """
    card_count = len(hand)

    if card_count == 0:
        return 0

    if card_count > 10:
        base_score = card_count * 2
    else:
        base_score = 0
        for card in hand:
            if card.rank in LOW_RANKS:
                base_score += 1
            elif card.rank in HIGH_RANKS:
                base_score += 2
            elif card.rank == "2":
                pass

    has_two = any(card.rank == "2" for card in hand)
    if has_two:
        base_score *= 2

    return base_score


def update_round_scores(players: list):
    """
    Add each player's round penalty to total_score.

    Return a list of round result dictionaries for the GUI.
    """
    round_results = []

    for player in players:
        round_penalty = calculate_score(player.hand)
        player.total_score += round_penalty
        round_results.append({
            "name": player.name,
            "round_penalty": round_penalty,
            "total_score": player.total_score,
            "cards_left": len(player.hand)
        })

    return round_results


def check_match_loser(players: list, limit: int = 150):
    """
    Return the first player whose total score is greater than or equal to limit.
    Return None if no player has reached the limit.
    """
    for player in players:
        if player.total_score >= limit:
            return player

    return None
