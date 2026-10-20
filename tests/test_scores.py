import time

import pytest

from house.interpreter import run_script
from house.layout_format import parse_layout
from house.scores import Scores, score
from tests.test_interpreter import CHAIN_SCRIPT, EXAMPLE_SCRIPT


def scores_of(script, start=None):
    result = run_script(script, start)
    assert result.accepted
    return result.scores


def test_example_house(example_text):
    assert score(parse_layout(example_text)) == Scores(0, 0.0, 1.8, 0)


def test_chain_house_scores_badly():
    assert scores_of(CHAIN_SCRIPT) == Scores(corridor_rooms=6, privacy_order=0.0, walking_distance=2.0, compactness=2)


def test_corridor_counts_only_forced_passages():
    # R4 can be reached through the kitchen R3 or through bedroom R2, so neither is a forced passage.
    assert scores_of("room R1 living room A1\nroom R2 bedroom A2\nroom R3 kitchen B1\nroom R4 bedroom B2\n"
                     "door A1|north\ndoor A1|A2\ndoor A1|B1\ndoor B1|B2\ndoor A2|B2\n").corridor_rooms == 0


def test_bathroom_only_through_a_bedroom():
    s = scores_of("room R1 living room A1\nroom R2 bedroom A2\nroom R3 bathroom A3\n"
                  "door A1|north\ndoor A1|A2\ndoor A2|A3\n")
    assert s.corridor_rooms == 1


def test_a_kitchen_is_a_passage_too():
    s = scores_of("room R1 living room A1\nroom R2 kitchen A2\nroom R3 bedroom A3\n"
                  "door A1|north\ndoor A1|A2\ndoor A2|A3\n")
    assert s.corridor_rooms == 1


def test_living_rooms_may_be_passed_through():
    s = scores_of("room R1 living room A1\nroom R2 living room A2\nroom R3 bedroom A3\nroom R4 kitchen B1\n"
                  "door A1|north\ndoor A1|A2\ndoor A2|A3\ndoor A1|B1\n")
    assert s.corridor_rooms == 0


def test_houses_of_the_5x5_run_still_load_and_their_hallways_may_be_passed_through(example_text):
    s = score(parse_layout(example_text.replace("R3  living room   B1", "R3  hallway       B1")))
    assert s == Scores(0, 0.0, 1.8, 0)


def test_privacy_bathroom_beside_kitchen_off_living_room_is_a_tie():
    s = scores_of("room R1 living room A1\nroom R2 kitchen A2\nroom R3 bathroom B1\n"
                  "door A1|north\ndoor A1|A2\ndoor A1|B1\n")
    assert s.privacy_order == 0.25


def test_privacy_bedroom_nearer_than_kitchen_is_wrong():
    s = scores_of("room R1 living room A1\nroom R2 bedroom A2\nroom R3 kitchen A3\n"
                  "door A1|north\ndoor A1|A2\ndoor A2|A3\n")
    assert s.privacy_order == 0.5     # (R1,R2) fine, (R3,R2): bedroom is nearer


def test_privacy_is_zero_without_pairs():
    assert scores_of("room R1 living room A1\ndoor A1|north\n").privacy_order == 0.0


def test_compactness_sticking_out():
    assert scores_of("room R1 living room A1\nroom R2 kitchen A2\nroom R3 bedroom B1\nroom R4 bedroom B2\n"
                     "door A1|north\ndoor A1|A2\ndoor A1|B1\ndoor B1|B2\n").compactness == 0
    assert scores_of("room R1 living room A1\nroom R2 kitchen A2\nroom R3 bedroom A3\nroom R4 bedroom A4\n"
                     "door A1|north\ndoor A1|A2\ndoor A2|A3\ndoor A3|A4\n").compactness == 2


def test_invalid_house_has_no_scores():
    assert scores_of("room R1 living room A1\nroom R2 bedroom A2\ndoor A1|north\n") is None


def test_scoring_takes_milliseconds(example_text):
    layout = parse_layout(example_text)
    start = time.perf_counter()
    for _ in range(100):
        score(layout)
    assert (time.perf_counter() - start) / 100 < 0.01


def test_walking_distance_is_the_average_over_every_pair_of_rooms():
    # living room with three rooms around it: pairs (living, x) = 1 each, pairs (x, y) = 2 each -> (3*1 + 3*2) / 6
    star = scores_of("room R1 living room B2\nroom R2 kitchen A2\nroom R3 bedroom B1\nroom R4 bedroom B3\n"
                     "door B2|south\ndoor A2|B2\ndoor B1|B2\ndoor B2|B3\n")
    assert star.walking_distance == 1.5
    # the same four rooms in a row: distances 1,2,3,1,2,1 -> 10 / 6
    row = scores_of("room R1 living room A1\nroom R2 kitchen A2\nroom R3 bedroom A3\nroom R4 bedroom A4\n"
                    "door A1|north\ndoor A1|A2\ndoor A2|A3\ndoor A3|A4\n")
    assert row.walking_distance == 1.6667


def test_walking_distance_counts_trips_that_do_not_start_at_the_entrance():
    # bathroom and bedroom both hang off the living room: the trip between them goes through it (2 doors)
    s = scores_of("room R1 living room A1\nroom R2 bathroom A2\nroom R3 bedroom B1\n"
                  "door A1|north\ndoor A1|A2\ndoor A1|B1\n")
    assert s.walking_distance == round((1 + 1 + 2) / 3, 4)


def test_one_room_has_no_walking_distance():
    assert scores_of("room R1 living room A1\ndoor A1|north\n").walking_distance == 0.0
