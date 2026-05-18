import argparse
import copy
import random
from statistics import mean

from ai_policy import DEFAULT_WEIGHTS, SmartAIPolicy
from game import Game
from player import Player


def make_players(num_players):
    return [Player(f"Player {i + 1}") for i in range(num_players)]


def get_total_score(player):
    return getattr(player, "total_score", getattr(player, "score", 0))


def apply_ai_move(game, player, move):
    player.remove_cards(move)
    game.current_table = move
    game.last_player_index = game.current_player_index
    game.pass_count = 0
    game.status_message = f"{player.name} played {' '.join(str(card) for card in move)}."

    if player.has_no_cards():
        game.round_winner = player
        return

    game.next_player()


def apply_ai_pass(game, player):
    if not game.current_table:
        game.status_message = f"{player.name} could not make a move."
        game.next_player()
        return

    drawn_card = game.draw_one_card(player)
    game.pass_count += 1

    if drawn_card:
        game.status_message = f"{player.name} passed and drew {drawn_card}."
    else:
        game.status_message = f"{player.name} passed. The draw pile is empty."

    game.next_player()

    if game.pass_count >= len(game.players) - 1:
        game.current_table = []
        game.pass_count = 0
        game.current_player_index = game.last_player_index
        game.status_message = "All other players passed. The table has been reset."


def play_training_match(candidate_policy, opponent_policy, target_seat, num_players=4, max_turns=20000):
    """
    Play one complete match.

    target_seat uses candidate_policy.
    Other seats use opponent_policy.

    Lower score is better because your scoring system makes the player who
    reaches 150 lose the match.
    """
    players = make_players(num_players)
    game = Game(players, ai_policy=None, use_trained_ai=False)
    game.deal_new_round()

    turns = 0
    while not game.game_over and turns < max_turns:
        turns += 1

        player = game.get_current_player()
        seat = game.players.index(player)

        if seat == target_seat:
            move = candidate_policy.choose_move(game, player)
        else:
            move = opponent_policy.choose_move(game, player)

        if move:
            apply_ai_move(game, player, move)
        else:
            apply_ai_pass(game, player)

        if game.round_winner:
            game.end_round_and_prepare_next()

    target = game.players[target_seat]
    target_score = get_total_score(target)
    other_scores = [
        get_total_score(p)
        for i, p in enumerate(game.players)
        if i != target_seat
    ]

    loser = game.match_loser
    target_lost = loser is target

    reward = 0.0
    reward -= target_score
    reward += mean(other_scores) * 0.35

    if not target_lost:
        reward += 90.0
    else:
        reward -= 180.0

    all_scores = [get_total_score(p) for p in game.players]
    if target_score == min(all_scores):
        reward += 45.0

    if turns >= max_turns:
        reward -= 60.0

    return reward


def evaluate_policy(weights, games, num_players=4, seed=None):
    if seed is not None:
        random.seed(seed)

    candidate = SmartAIPolicy(weights, exploration=0.03)
    opponent = SmartAIPolicy(DEFAULT_WEIGHTS, exploration=0.08)

    rewards = []
    for i in range(games):
        target_seat = i % num_players
        rewards.append(
            play_training_match(
                candidate,
                opponent,
                target_seat=target_seat,
                num_players=num_players,
            )
        )

    return mean(rewards)


def mutate_weights(weights, strength=0.18):
    mutated = copy.deepcopy(weights)

    for key, value in mutated.items():
        if key == "randomness":
            continue

        noise = random.gauss(0, strength)
        new_value = value * (1.0 + noise)

        if key in {
            "low_power",
            "play_more_cards",
            "high_power_when_danger",
            "finish_round",
            "keep_two_early",
            "keep_high_card_early",
            "avoid_break_pair",
            "avoid_break_triple",
            "five_card_bonus",
            "empty_table_combo_bonus",
            "block_opponent",
        }:
            new_value = max(0.0, min(250.0, new_value))

        mutated[key] = round(new_value, 4)

    return mutated


def train(total_games=10000, num_players=4, population=12, games_per_candidate=12, output=None):
    random.seed()

    if output is None:
        output = f"ai_weights_{num_players}p.json"

    best_weights = copy.deepcopy(DEFAULT_WEIGHTS)
    best_score = evaluate_policy(best_weights, games=max(4, games_per_candidate // 2), num_players=num_players)

    games_used = max(4, games_per_candidate // 2)
    generation = 0

    print(f"Initial score: {best_score:.2f}")

    while games_used < total_games:
        generation += 1
        candidates = [best_weights]

        for _ in range(population - 1):
            strength = max(0.04, 0.22 * (1.0 - games_used / max(1, total_games)))
            candidates.append(mutate_weights(best_weights, strength=strength))

        results = []
        for weights in candidates:
            if games_used >= total_games:
                break

            games_now = min(games_per_candidate, total_games - games_used)
            score = evaluate_policy(weights, games=games_now, num_players=num_players)
            games_used += games_now
            results.append((score, weights))

        results.sort(key=lambda item: item[0], reverse=True)

        if results and results[0][0] > best_score:
            best_score = results[0][0]
            best_weights = results[0][1]

        if generation % 5 == 0 or games_used >= total_games:
            print(
                f"Generation {generation:03d} | "
                f"games {games_used}/{total_games} | "
                f"best score {best_score:.2f}"
            )

    final_policy = SmartAIPolicy(best_weights)
    final_policy.save(
        output,
        metadata={
            "training_games": total_games,
            "num_players": num_players,
            "best_score": best_score,
            "population": population,
            "games_per_candidate": games_per_candidate,
        },
    )

    print(f"Saved trained weights to {output}")
    print(best_weights)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=10000)
    parser.add_argument("--players", type=int, default=4, choices=[2, 3, 4])
    parser.add_argument("--population", type=int, default=12)
    parser.add_argument("--games-per-candidate", type=int, default=12)
    parser.add_argument(
        "--output",
        default=None,
        help="Output weights file. If omitted, this becomes ai_weights_2p.json, ai_weights_3p.json, or ai_weights_4p.json.",
    )
    args = parser.parse_args()

    train(
        total_games=args.games,
        num_players=args.players,
        population=args.population,
        games_per_candidate=args.games_per_candidate,
        output=args.output,
    )


if __name__ == "__main__":
    main()
