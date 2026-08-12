from __future__ import annotations

from app.prompts import CATEGORIES, random_prompt


def test_random_prompt_returns_a_prompt_for_every_category():
    for category in CATEGORIES:
        prompt = random_prompt(category)
        assert isinstance(prompt, str) and prompt


def test_random_prompt_falls_back_to_general_for_unknown_category():
    prompt = random_prompt("Not A Real Category")
    assert isinstance(prompt, str) and prompt
