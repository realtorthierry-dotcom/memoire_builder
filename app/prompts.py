from __future__ import annotations

import random
import string

CATEGORIES = [
    "Freeform",
    "Childhood",
    "Wartime Experiences",
    "Love & Marriage",
    "Career & Work",
    "Family",
    "Travel & Adventures",
    "Challenges & Lessons Learned",
    "Advice for Future Generations",
]

_PROMPTS: dict[str, list[str]] = {
    "Freeform": [
        "Just say whatever comes to mind — there's no right place to start.",
        "Talk about anything you're thinking about right now.",
        "No topic in mind? That's alright — just start talking and see where it goes.",
    ],
    "Childhood": [
        "What was the house you grew up in like?",
        "Who was your best friend as a child, and what did you two get up to?",
        "What's your earliest memory?",
        "What did your family do together on weekends?",
        "Did you have a favorite toy, game, or place to play?",
    ],
    "Family": [
        "Tell me about your parents — what were they like?",
        "What's a family tradition you remember fondly?",
        "Tell me about your brothers or sisters.",
        "What's something you learned from a grandparent?",
        "What was it like when your own children were born?",
    ],
    "Wartime Experiences": [
        "What do you remember about the war years?",
        "Where were you when the war began, and how did it change daily life?",
        "Did you or someone close to you serve? What was that like?",
        "How did your family manage during rationing or hard times?",
        "Is there a moment from that time that stays with you?",
        "How do you think that time shaped who you became?",
    ],
    "Career & Work": [
        "What was your first job?",
        "What work are you most proud of?",
        "Tell me about a mentor or boss who shaped how you work.",
        "What was a typical workday like for you?",
        "Did your career turn out the way you expected?",
    ],
    "Love & Marriage": [
        "How did you meet your partner?",
        "What do you remember about your wedding day?",
        "What's the secret to a lasting relationship, in your experience?",
        "Tell me about a moment you fell in love all over again.",
    ],
    "Challenges & Lessons Learned": [
        "What's the hardest thing you've ever gone through?",
        "What's a mistake that taught you something important?",
        "How did you get through a difficult time in your life?",
        "What would you tell your younger self?",
    ],
    "Travel & Adventures": [
        "What's the most memorable trip you've ever taken?",
        "Is there a place you visited that changed how you saw the world?",
        "Tell me about an adventure or something a little reckless you did.",
    ],
    "Advice for Future Generations": [
        "What do you want your grandchildren to know about you?",
        "What's the best advice anyone ever gave you?",
        "What do you hope people remember about you?",
        "What does a good life mean to you?",
    ],
}


def prompts_for(category: str) -> list[str]:
    return _PROMPTS.get(category, _PROMPTS["Freeform"])


def random_prompt(category: str) -> str:
    return random.choice(prompts_for(category))


def lettered_categories() -> list[tuple[str, str]]:
    """Categories paired with A, B, C... labels, in curated (not alphabetical)
    order for easier listening and selection than a long unbroken list."""
    return list(zip(string.ascii_uppercase, CATEGORIES))


def category_options() -> list[str]:
    """Display strings like 'A. Childhood', in curated order."""
    return [f"{letter}. {category}" for letter, category in lettered_categories()]


def category_from_option(option: str) -> str:
    """Recovers the plain category name from a 'A. Childhood'-style display string."""
    return option.split(". ", 1)[1]


def spoken_category_list() -> str:
    """A spoken-friendly listing of every category with its letter, for reading aloud."""
    lines = [
        f"{letter}, {category.replace('&', 'and')}" for letter, category in lettered_categories()
    ]
    return "What would you like to talk about? " + ". ".join(lines) + "."
