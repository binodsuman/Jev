"""Read Jev's numbers and choose fast, capable, or refuse."""


# Look at the task label, its confidence, its probabilities, and the complexity score.
# Returns two strings: the route ("fast", "capable", or "refuse") and a short reason.
# This function never sees the raw user sentence, so the user cannot pick the model.
def decide(answers):
    choice = answers["task"]["choice"]
    confidence = answers["task"]["confidence"]
    probabilities = answers["task"]["probabilities"]
    score = answers["complexity"]["score"]

    # A selected "unsupported" label, or a 50%+ chance of that label, stops here.
    if choice == "unsupported" or probabilities.get("unsupported", 0) >= 0.5:
        return "refuse", "unsupported request"

    if choice == "coding":
        return "capable", "coding task"

    if choice == "reasoning":
        return "capable", "complex reasoning"

    # Flash-Lite is allowed only when the label is simple, Jev is confident,
    # and the score is still on the easy half of the scale (below 1.5).
    if choice == "simple" and confidence >= 0.70 and score < 1.5:
        return "fast", "simple question"

    # Low confidence, a high score, or an unexpected label uses the stronger model.
    return "capable", "not sure, or too hard for the cheap model"
