"""Pure decision logic for the student-led, four-stage teaching journey."""
from __future__ import annotations

LEVELS = {
    1: "Definition & detailed explanation",
    2: "Simple explanation",
    3: "Real-world example",
    4: "Explain like I'm 10",
}
LOW_SCORE_THRESHOLD = 60


def next_level(current: int) -> int:
    """Only move forward, stopping at the simplest teaching stage."""
    if current not in LEVELS:
        raise ValueError("Teaching level must be between 1 and 4")
    return min(current + 1, 4)


def quiz_percentage(correct: int, total: int) -> int:
    if total <= 0 or not 0 <= correct <= total:
        raise ValueError("Quiz scores must satisfy 0 <= correct <= total and total > 0")
    return round(100 * correct / total)


def needs_tutor_invite(correct: int, total: int) -> bool:
    """Invite a student to optional remedial tutoring after a low quiz score."""
    return quiz_percentage(correct, total) < LOW_SCORE_THRESHOLD


def missed_questions(questions: list[dict], results: list[dict]):
    if len(questions) != len(results):
        raise ValueError("Questions and results must have the same length")
    return [(i, question, outcome) for i, (question, outcome) in
            enumerate(zip(questions, results)) if not outcome["correct"]]


def retry_missed_quiz(quiz: dict, epoch: int) -> dict:
    """Create a separately graded retry containing only the missed questions."""
    missed = missed_questions(quiz["questions"], quiz["results"])
    if not missed:
        raise ValueError("There are no missed questions to retry")
    return {
        **quiz,
        "questions": [question for _, question, _ in missed],
        "graded": False,
        "results": [],
        "epoch": epoch,
        "is_retry": True,
    }


def review_payload(topic: str, question: dict, result: dict, passages: list[dict]):
    """Create grounded feedback context from the specific missed MCQ."""
    source_id = question["source_id"]
    evidence = next((passage for passage in passages if passage["marker"] == source_id), None)
    if evidence is None:
        raise ValueError("Could not locate the evidence for this quiz question")
    return {
        "topic": topic,
        "quiz_question": question["question"],
        "chosen_answer": question["options"][result["selected"]],
        "correct_answer": question["options"][question["answer_index"]],
        "source_id": source_id,
        "evidence": evidence,
    }
