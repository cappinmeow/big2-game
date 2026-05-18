import json
import os
import random
from collections import defaultdict

from rules import is_valid_play, get_play_type


DEFAULT_WEIGHTS = {
    "play_more_cards": 26.0,
    "low_power": 11.0,
    "high_power_when_danger": 18.0,
    "finish_round": 140.0,
    "keep_two_early": 72.0,
    "keep_high_card_early": 22.0,
    "avoid_break_pair": 20.0,
    "avoid_break_triple": 32.0,
    "five_card_bonus": 34.0,
    "empty_table_combo_bonus": 18.0,
    "block_opponent": 58.0,
    "randomness": 2.5,
}


class SmartAIPolicy:
    """
    Weight-based Big 2 AI policy.

    The model does not need pygame. It can be used by the normal game screen and
    by self_play_train.py.

    Main idea:
    - Generate all legal moves from Game's existing helper methods.
    - Score each move with learned weights.
    - Choose the highest scoring move.
    """

    def __init__(self, weights=None, exploration=0.0):
        self.weights = dict(DEFAULT_WEIGHTS)
        if weights:
            self.weights.update(weights)
        self.exploration = exploration

    @classmethod
    def load(cls, path="ai_weights.json", exploration=0.0):
        if not os.path.exists(path):
            return cls(exploration=exploration)

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict) and "weights" in data:
                return cls(data["weights"], exploration=exploration)

            if isinstance(data, dict):
                return cls(data, exploration=exploration)

        except Exception:
            pass

        return cls(exploration=exploration)

    @classmethod
    def load_default(cls):
        return cls.load("ai_weights.json", exploration=0.0)

    @classmethod
    def load_for_player_count(cls, num_players, exploration=0.0):
        """
        Load the AI weights that match the current player count.

        Priority:
        1. ai_weights_2p.json / ai_weights_3p.json / ai_weights_4p.json
        2. ai_weights.json
        3. DEFAULT_WEIGHTS inside this file
        """
        player_count_path = f"ai_weights_{num_players}p.json"

        if os.path.exists(player_count_path):
            return cls.load(player_count_path, exploration=exploration)

        return cls.load("ai_weights.json", exploration=exploration)

    def save(self, path="ai_weights.json", metadata=None):
        payload = {
            "weights": self.weights,
            "metadata": metadata or {},
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def choose_move(self, game, player):
        candidates = self._legal_candidates(game, player)

        if not candidates:
            return None

        if self.exploration > 0 and random.random() < self.exploration:
            return random.choice(candidates)

        scored = [(self.score_move(game, player, move), move) for move in candidates]
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[0][1]

    def _legal_candidates(self, game, player):
        if not player.hand:
            return []

        finishing_play = game.get_finishing_play(player)
        if finishing_play:
            return [finishing_play]

        if not game.current_table:
            candidates = game.get_all_candidate_plays(player.hand)

            # Respect the first-play rule: the opening play must include 3♦ or
            # the required lowest card when 3♦ is not in any player's hand.
            if game.is_first_play_of_round():
                required_card = game.get_required_opening_card()
                if required_card is not None:
                    candidates = [
                        move for move in candidates
                        if required_card in move
                    ]

            return candidates

        table_size = len(game.current_table)

        if table_size == 1:
            candidates = [[card] for card in sorted(player.hand, key=lambda card: card.sort_key())]
        elif table_size == 2:
            candidates = game.get_pairs(player.hand)
        elif table_size == 3:
            candidates = game.get_triples(player.hand)
        elif table_size == 5:
            candidates = game.get_five_card_plays(player.hand)
        else:
            return []

        return [
            candidate for candidate in candidates
            if is_valid_play(candidate, game.current_table)
        ]

    def score_move(self, game, player, move):
        weights = self.weights
        move = sorted(move, key=lambda card: card.sort_key())

        score = 0.0
        score += len(move) * weights["play_more_cards"]

        power = self._move_power(game, move)
        score -= power * weights["low_power"]

        if len(move) == len(player.hand):
            score += weights["finish_round"]

        if self._opponent_in_danger(game, player):
            score += power * weights["high_power_when_danger"]
            score += weights["block_opponent"]

        if self._contains_rank(move, "2") and len(player.hand) > 4:
            score -= weights["keep_two_early"]

        if self._contains_high_card(move) and len(player.hand) > 6:
            score -= weights["keep_high_card_early"]

        break_pair, break_triple = self._combo_break_cost(player.hand, move)
        score -= break_pair * weights["avoid_break_pair"]
        score -= break_triple * weights["avoid_break_triple"]

        play_type = get_play_type(move)
        if len(move) == 5 and play_type is not None:
            score += weights["five_card_bonus"]

        if not game.current_table and len(move) > 1:
            score += weights["empty_table_combo_bonus"]

        if self.exploration > 0:
            score += random.uniform(-weights["randomness"], weights["randomness"])

        return score

    def _move_power(self, game, move):
        key = game.play_sort_key(move)

        total = 0.0
        for value in key:
            if isinstance(value, (int, float)):
                total = total * 20.0 + float(value)

        return total / 100.0

    def _contains_rank(self, move, rank):
        return any(card.rank == rank for card in move)

    def _contains_high_card(self, move):
        return any(card.rank in {"A", "K", "2"} for card in move)

    def _opponent_in_danger(self, game, player):
        for other in game.players:
            if other is not player and len(other.hand) <= 3:
                return True
        return False

    def _combo_break_cost(self, hand, move):
        hand_groups = defaultdict(int)
        move_groups = defaultdict(int)

        for card in hand:
            hand_groups[card.rank] += 1

        for card in move:
            move_groups[card.rank] += 1

        break_pair = 0
        break_triple = 0

        for rank, hand_count in hand_groups.items():
            used = move_groups.get(rank, 0)

            if used == 0:
                continue

            # Playing the whole combo is not treated as breaking it.
            if used >= hand_count:
                continue

            if hand_count >= 2:
                break_pair += 1

            if hand_count >= 3:
                break_triple += 1

        return break_pair, break_triple
