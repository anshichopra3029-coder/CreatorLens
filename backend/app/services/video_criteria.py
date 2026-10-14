"""Evaluation rules sent with every video-analysis request.

These are instructions for the model. They are not scores, and they do not
invent observations.
"""

from __future__ import annotations

COMMON_CHECKS: tuple[str, ...] = (
    "Speech or primary audio can be understood.",
    "The main subject stays visible long enough to follow.",
    "The opening makes the point of the video clear.",
    "The useful part is not buried by a long unrelated opening.",
)

CATEGORY_CRITERIA: dict[str, tuple[str, ...]] = {
    "Education": (
        "The video states what the viewer should learn.",
        "Each idea is explained before the next one is introduced.",
        "A worked example or demonstration is shown, not only announced.",
        "The ending gives the viewer a way to check or apply the lesson.",
    ),
    "Vlog": (
        "The video establishes who is present and where they are.",
        "The clips share one through-line instead of unrelated moments.",
        "Speech remains understandable over ambient sound.",
        "Jumps in time or place are signposted.",
    ),
    "Recipe": (
        "Ingredients and amounts are shown or stated before they are used.",
        "The steps appear in an order someone could cook from.",
        "The technique is visible, not only described.",
        "The finished result, or a clear doneness cue, is shown.",
    ),
    "Product Review": (
        "The product is named.",
        "The product is shown in use, not only in its packaging.",
        "Observed facts are separated from opinion.",
        "The video says who the product does and does not suit.",
    ),
}


def criteria_for(category: str) -> list[str]:
    specific = CATEGORY_CRITERIA[category]
    return [f"Common: {item}" for item in COMMON_CHECKS] + [
        f"{category}: {item}" for item in specific
    ]


def criteria_prompt() -> str:
    lines = [
        "Choose exactly one category: Education, Vlog, Recipe, or Product Review.",
        "Apply every common check. Also apply only the criteria for the category you choose.",
        "Base every strength, suggestion, and evidence item on something visible or audible.",
        "Do not invent a lesson, place, ingredient, or product that the video does not show.",
        "Use MM:SS for timestamps. Use an empty string when you cannot locate the moment.",
        "In confidence_note, say what you are unsure about. If the category is uncertain, say so.",
        "",
        "Common checks:",
    ]
    lines.extend(f"- {item}" for item in COMMON_CHECKS)
    for category, checks in CATEGORY_CRITERIA.items():
        lines.append("")
        lines.append(f"{category} criteria:")
        lines.extend(f"- {item}" for item in checks)
    return "\n".join(lines)
