from __future__ import annotations

from app.prompts import (
    CATEGORIES,
    category_from_option,
    category_options,
    random_prompt,
    spoken_category_list,
)


def test_random_prompt_returns_a_prompt_for_every_category():
    for category in CATEGORIES:
        prompt = random_prompt(category)
        assert isinstance(prompt, str) and prompt


def test_random_prompt_falls_back_to_freeform_for_unknown_category():
    prompt = random_prompt("Not A Real Category")
    assert isinstance(prompt, str) and prompt


def test_spoken_category_list_mentions_every_category_without_ampersands():
    listing = spoken_category_list()
    assert "&" not in listing
    for category in CATEGORIES:
        assert category.replace("&", "and") in listing


def test_category_options_follow_curated_order_and_are_lettered():
    options = category_options()
    names = [category_from_option(option) for option in options]

    assert names == CATEGORIES
    assert options[0] == "A. Freeform"
    assert options[1] == "B. Childhood"


def test_category_from_option_round_trips():
    for option in category_options():
        assert category_from_option(option) in CATEGORIES
