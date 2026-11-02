import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

df = pd.read_csv("gcse_biology_questions.csv")


def assess_answer(student_answer, question_text):
    """
    Use TF-IDF to extract key biological terms from the mark scheme,
    then check how many appear in the student's answer.

    Returns:
        score (float): 0.0 to 1.0
        missing_terms (list): key terms the student did not use
        found_terms (list): key terms the student did use
    """
    # Find the mark scheme answer for this question
    matches = df[df['question'].str.strip().str.lower() == question_text.strip().lower()]

    if matches.empty:
        # Try partial match if exact match fails
        matches = df[df['question'].str.lower().str.contains(
            question_text.strip().lower()[:40], na=False
        )]

    if matches.empty:
        return None, [], []

    mark_scheme = matches.iloc[0]['mark_scheme_answer']

    # Use TF-IDF to identify the most important terms in the mark scheme
    try:
        vectorizer = TfidfVectorizer(stop_words='english', max_features=8)
        vectorizer.fit([mark_scheme])
        key_terms = list(vectorizer.get_feature_names_out())
    except Exception:
        return None, [], []

    if not key_terms:
        return None, [], []

    # Check which key terms appear in the student's answer
    student_lower = student_answer.lower()
    found = [term for term in key_terms if term in student_lower]
    missing = [term for term in key_terms if term not in student_lower]

    score = round(len(found) / len(key_terms), 2)
    return score, missing, found


def get_feedback_label(score):
    """
    Convert a numerical score into a strength label
    for injection into the system prompt.
    """
    if score is None:
        return "unknown"
    if score >= 0.7:
        return "strong"
    elif score >= 0.4:
        return "partial"
    else:
        return "weak"


def format_assessment_for_prompt(score, missing_terms, found_terms):
    """
    Format assessment results as a string to inject into the system prompt.
    """
    if score is None:
        return ""

    strength = get_feedback_label(score)

    return f"""
AUTOMATED ASSESSMENT OF STUDENT'S LAST ANSWER:
Score: {score:.0%} of key mark scheme terms used
Strength: {strength}
Key terms student used: {', '.join(found_terms) if found_terms else 'none identified'}
Key terms student missed: {', '.join(missing_terms) if missing_terms else 'none'}

Use this assessment to calibrate your response:
- If strength is 'strong': acknowledge and increase difficulty
- If strength is 'partial': acknowledge what they got right, hint at missing terms
- If strength is 'weak': move down a scaffolding tier, do not reveal the missing terms directly
""".strip()


# Test 
if __name__ == "__main__":
    question = "What is the function of the mitochondria?"
    
    print("Test 1 — Strong answer:")
    answer1 = "The mitochondria is the site of aerobic respiration which releases energy as ATP for the cell"
    score, missing, found = assess_answer(answer1, question)
    print(f"Score: {score}, Found: {found}, Missing: {missing}")

    print("\nTest 2 — Weak answer:")
    answer2 = "it gives the cell energy"
    score, missing, found = assess_answer(answer2, question)
    print(f"Score: {score}, Found: {found}, Missing: {missing}")
