from collections import defaultdict
from itertools import combinations

from deck import Deck
from rules import is_valid_play, get_play_type
from scoring import update_round_scores, check_match_loser

try:
    from ai_policy import SmartAIPolicy
except ImportError:
    SmartAIPolicy = None


class Game:
    def __init__(self, players, ai_policy=None, use_trained_ai=True):
        self.players = players
        self.current_player_index = 0
        self.current_table = []
        self.last_player_index = None
        self.pass_count = 0
        self.round_number = 1
        self.game_over = False
        self.match_loser = None
        self.round_winner = None
        self.status_message = ""
        self.draw_pile = []
        self.ai_policy = ai_policy
        if self.ai_policy is None and use_trained_ai and SmartAIPolicy is not None:
            self.ai_policy = SmartAIPolicy.load_for_player_count(len(self.players))

    def get_current_player(self):
        return self.players[self.current_player_index]

    def next_player(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def deal_new_round(self):
        deck = Deck()
        deck.shuffle()
        hands, remaining_deck = deck.deal(
            num_players=len(self.players),
            cards_each=13
        )

        for player, hand in zip(self.players, hands):
            player.hand = []
            player.receive_cards(hand)

        self.draw_pile = remaining_deck
        self.current_table = []
        self.last_player_index = None
        self.pass_count = 0
        self.round_winner = None
        self.status_message = f"Round {self.round_number} started."

        # Rule 1: the player with 3♦ starts.
        for i, player in enumerate(self.players):
            for card in player.hand:
                if str(card) == "3♦":
                    self.current_player_index = i
                    self.status_message = (
                        f"Round {self.round_number} started. "
                        f"{player.name} has 3♦ and goes first."
                    )
                    return

        # Rule 2: if nobody has 3♦, the player with the smallest card starts.
        smallest_player_index = 0
        smallest_card = min(self.players[0].hand, key=lambda card: card.sort_key())

        for i, player in enumerate(self.players[1:], start=1):
            player_smallest = min(player.hand, key=lambda card: card.sort_key())
            if player_smallest.sort_key() < smallest_card.sort_key():
                smallest_card = player_smallest
                smallest_player_index = i

        self.current_player_index = smallest_player_index
        self.status_message = (
            f"Round {self.round_number} started. "
            f"No player has 3♦, so {self.players[smallest_player_index].name} goes first "
            f"with the lowest card ({smallest_card})."
        )

    def draw_one_card(self, player):
        if self.draw_pile:
            drawn_card = self.draw_pile.pop(0)
            player.receive_cards([drawn_card])
            return drawn_card

        return None

    # ------------------------------------------------------------------
    # AI helper methods
    # ------------------------------------------------------------------

    def pair_sort_key(self, pair):
        """
        Sort pairs using the same idea as the rules module:
        pair rank first, then the highest suit inside the pair.
        """
        sorted_pair = sorted(pair, key=lambda card: card.sort_key())
        highest_card = sorted_pair[-1]
        return highest_card.rank_value(), highest_card.suit_value()

    def triple_sort_key(self, triple):
        """
        Triples are compared by rank. The highest suit is only used as a
        deterministic tie-breaker for sorting generated candidates.
        """
        sorted_triple = sorted(triple, key=lambda card: card.sort_key())
        highest_card = sorted_triple[-1]
        return highest_card.rank_value(), highest_card.suit_value()

    def get_pairs(self, hand):
        """
        Return every possible pair in the hand.

        This is more complete than returning only the lowest pair for each rank.
        For example, if the AI has Q♦ Q♣ Q♥ Q♠, it can now consider all six
        possible Q pairs and choose the smallest pair that can beat the table.
        """
        groups = defaultdict(list)
        for card in hand:
            groups[card.rank].append(card)

        pairs = []
        for rank_cards in groups.values():
            if len(rank_cards) >= 2:
                sorted_cards = sorted(rank_cards, key=lambda card: card.sort_key())
                for pair in combinations(sorted_cards, 2):
                    pairs.append(list(pair))

        pairs.sort(key=self.pair_sort_key)
        return pairs

    def get_triples(self, hand):
        """
        Return every possible triple in the hand.
        """
        groups = defaultdict(list)
        for card in hand:
            groups[card.rank].append(card)

        triples = []
        for rank_cards in groups.values():
            if len(rank_cards) >= 3:
                sorted_cards = sorted(rank_cards, key=lambda card: card.sort_key())
                for triple in combinations(sorted_cards, 3):
                    triples.append(list(triple))

        triples.sort(key=self.triple_sort_key)
        return triples

    def get_five_card_plays(self, hand):
        """
        Return all valid five-card plays in the hand, sorted from weaker to stronger.
        """
        five_card_plays = []

        for combo in combinations(hand, 5):
            combo_list = sorted(list(combo), key=lambda card: card.sort_key())
            play_type = get_play_type(combo_list)

            if play_type in {
                "straight",
                "flush",
                "full_house",
                "four_of_a_kind",
                "straight_flush",
            }:
                five_card_plays.append(combo_list)

        unique_plays = []
        seen = set()

        for play in five_card_plays:
            key = tuple(str(card) for card in play)
            if key not in seen:
                seen.add(key)
                unique_plays.append(play)

        unique_plays.sort(key=self.play_sort_key)
        return unique_plays

    def play_sort_key(self, play):
        """
        Sort valid plays so the AI can choose the smallest useful move.

        The key is aligned with the rules module:
        - Singles compare rank, then suit.
        - Pairs compare pair rank, then the highest suit inside the pair.
        - Triples compare rank.
        - Five-card plays compare type strength, then their internal strength.
        """
        play = sorted(play, key=lambda card: card.sort_key())
        play_type = get_play_type(play)

        if len(play) == 1:
            card = play[0]
            return (1, card.rank_value(), card.suit_value())

        if len(play) == 2:
            pair_rank, pair_suit = self.pair_sort_key(play)
            return (2, pair_rank, pair_suit)

        if len(play) == 3:
            triple_rank, triple_suit = self.triple_sort_key(play)
            return (3, triple_rank, triple_suit)

        if len(play) == 5:
            type_rank = {
                "straight": 0,
                "flush": 1,
                "full_house": 2,
                "four_of_a_kind": 3,
                "straight_flush": 4,
            }[play_type]

            highest_card = play[-1]

            if play_type == "full_house":
                rank_counts = defaultdict(int)
                for card in play:
                    rank_counts[card.rank] += 1

                trip_rank = 0
                for card in play:
                    if rank_counts[card.rank] == 3:
                        trip_rank = card.rank_value()
                        break

                return (5, type_rank, trip_rank, 0)

            if play_type == "four_of_a_kind":
                rank_counts = defaultdict(int)
                for card in play:
                    rank_counts[card.rank] += 1

                quad_rank = 0
                for card in play:
                    if rank_counts[card.rank] == 4:
                        quad_rank = card.rank_value()
                        break

                return (5, type_rank, quad_rank, 0)

            return (5, type_rank, highest_card.rank_value(), highest_card.suit_value())

        return (99,)

    def get_all_candidate_plays(self, hand):
        """
        Generate all legal candidate plays the AI can make from this hand.
        """
        singles = [[card] for card in sorted(hand, key=lambda card: card.sort_key())]
        pairs = self.get_pairs(hand)
        triples = self.get_triples(hand)
        five_card_plays = self.get_five_card_plays(hand)

        candidates = singles + pairs + triples + five_card_plays
        candidates.sort(key=self.play_sort_key)
        return candidates

    def get_finishing_play(self, player):
        """
        If the AI can legally play all remaining cards in one move, return that move.

        This makes the AI finish the round immediately instead of wasting a turn
        with a smaller play.
        """
        hand = sorted(player.hand, key=lambda card: card.sort_key())

        if len(hand) not in (1, 2, 3, 5):
            return None

        if get_play_type(hand) is None:
            return None

        if is_valid_play(hand, self.current_table):
            return hand

        return None

    def choose_opening_play(self, player):
        """
        AI opening strategy when the table is empty.

        Priority:
        1. If the AI can finish immediately, do it.
        2. If the AI has 3♦, play the smallest legal move that contains 3♦.
        3. Otherwise, play the smallest legal move.

        This keeps the AI conservative while preventing it from missing obvious
        winning moves.
        """
        if not player.hand:
            return None

        if self.ai_policy is not None:
            policy_move = self.ai_policy.choose_move(self, player)
            if policy_move:
                return policy_move

        finishing_play = self.get_finishing_play(player)
        if finishing_play:
            return finishing_play

        candidates = self.get_all_candidate_plays(player.hand)

        has_three_diamond = any(str(card) == "3♦" for card in player.hand)
        if has_three_diamond:
            containing_three_diamond = [
                play for play in candidates
                if any(str(card) == "3♦" for card in play)
            ]

            if containing_three_diamond:
                containing_three_diamond.sort(key=self.play_sort_key)
                return containing_three_diamond[0]

        return candidates[0] if candidates else None

    def find_playable_cards(self, player):
        """
        Improved AI:
        - Empty table: choose a conservative opening play.
        - Non-empty table: choose the smallest legal play that beats the table.
        - If the AI can finish the round immediately, it always does so.
        - Pairs and triples are generated using all possible combinations, so the
          AI no longer misses valid same-rank suit upgrades.
        """
        if not player.hand:
            return None

        if self.ai_policy is not None:
            policy_move = self.ai_policy.choose_move(self, player)
            if policy_move:
                return policy_move

        finishing_play = self.get_finishing_play(player)
        if finishing_play:
            return finishing_play

        if not self.current_table:
            return self.choose_opening_play(player)

        table_size = len(self.current_table)

        if table_size == 1:
            candidates = [[card] for card in sorted(player.hand, key=lambda card: card.sort_key())]
        elif table_size == 2:
            candidates = self.get_pairs(player.hand)
        elif table_size == 3:
            candidates = self.get_triples(player.hand)
        elif table_size == 5:
            candidates = self.get_five_card_plays(player.hand)
        else:
            return None

        playable_candidates = [
            candidate for candidate in candidates
            if is_valid_play(candidate, self.current_table)
        ]

        if not playable_candidates:
            return None

        playable_candidates.sort(key=self.play_sort_key)
        return playable_candidates[0]

    def is_first_play_of_round(self):
        """
        Return True before the first legal play of a round has been made.
        """
        return (
            not self.current_table
            and self.last_player_index is None
            and self.pass_count == 0
        )

    def get_required_opening_card(self):
        """
        Return the card that must be included in the first play of the round.

        If 3♦ is in a player's hand, that card must be played by the starting
        player. If 3♦ is in the draw pile because fewer than four players are
        playing, the starting player's lowest card must be played.
        """
        for player in self.players:
            for card in player.hand:
                if str(card) == "3♦":
                    return card

        current_player = self.get_current_player()
        if not current_player.hand:
            return None

        return min(current_player.hand, key=lambda card: card.sort_key())

    def validate_opening_play(self, selected_cards):
        """
        Check whether the first play of the round follows the opening rule.
        """
        if not self.is_first_play_of_round():
            return True, ""

        required_card = self.get_required_opening_card()
        if required_card is None:
            return True, ""

        if required_card not in selected_cards:
            return False, f"The first play must include {required_card}."

        return True, ""

    # ------------------------------------------------------------------
    # Human and AI turn handling
    # ------------------------------------------------------------------

    def play_selected_cards(self, selected_cards):
        player = self.get_current_player()

        if self.game_over:
            return False, "The game is already over."

        if not player.is_human:
            return False, "It is not your turn."

        if not selected_cards:
            return False, "You have not selected any cards."

        opening_ok, opening_message = self.validate_opening_play(selected_cards)
        if not opening_ok:
            return False, opening_message

        if not is_valid_play(selected_cards, self.current_table):
            return False, "This is not a valid play."

        player.remove_cards(selected_cards)
        self.current_table = selected_cards
        self.last_player_index = self.current_player_index
        self.pass_count = 0
        self.status_message = f"{player.name} played {' '.join(str(card) for card in selected_cards)}."

        if player.has_no_cards():
            self.round_winner = player
            return True, "round_end"

        self.next_player()
        return True, "played"

    def pass_current_turn(self):
        player = self.get_current_player()

        if self.game_over:
            return False, "The game is already over."

        if not player.is_human:
            return False, "It is not your turn."

        if not self.current_table:
            return False, "You cannot pass when the table is empty."

        drawn_card = self.draw_one_card(player)
        self.pass_count += 1

        if drawn_card:
            self.status_message = f"{player.name} passed and drew {drawn_card}."
        else:
            self.status_message = f"{player.name} passed. The draw pile is empty."

        self.next_player()

        if self.pass_count >= len(self.players) - 1:
            self.current_table = []
            self.pass_count = 0
            self.current_player_index = self.last_player_index
            self.status_message = "All other players passed. The table has been reset."

        return True, "passed"

    def run_ai_until_human_turn(self):
        """
        Let AI players keep taking turns until it becomes the human player's turn
        or the round ends.

        If an AI cannot beat the current table, it passes and draws one card.
        """
        while not self.game_over and not self.round_winner:
            player = self.get_current_player()

            if player.is_human:
                break

            playable = self.find_playable_cards(player)

            if playable:
                player.remove_cards(playable)
                self.current_table = playable
                self.last_player_index = self.current_player_index
                self.pass_count = 0
                self.status_message = f"{player.name} played {' '.join(str(card) for card in playable)}."

                if player.has_no_cards():
                    self.round_winner = player
                    break

                self.next_player()

            else:
                if not self.current_table:
                    self.status_message = f"{player.name} could not make a move."
                    self.next_player()
                    continue

                drawn_card = self.draw_one_card(player)
                self.pass_count += 1

                if drawn_card:
                    self.status_message = f"{player.name} passed and drew {drawn_card}."
                else:
                    self.status_message = f"{player.name} passed. The draw pile is empty."

                self.next_player()

                if self.pass_count >= len(self.players) - 1:
                    self.current_table = []
                    self.pass_count = 0
                    self.current_player_index = self.last_player_index
                    self.status_message = "All other players passed. The table has been reset."

    def end_round_and_prepare_next(self):
        if not self.round_winner:
            return None

        results = update_round_scores(self.players)

        loser = check_match_loser(self.players, 150)
        if loser:
            self.game_over = True
            self.match_loser = loser
            self.status_message = f"{loser.name} reached 150 points and lost the match."
            return results

        self.round_number += 1
        self.deal_new_round()
        return results
