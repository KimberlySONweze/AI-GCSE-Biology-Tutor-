import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load dataset
df = pd.read_csv("gcse_biology_questions.csv")

# Load embedding model
print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Embed all questions once at startup
print("Embedding questions...")
question_embeddings = model.encode(df['question'].tolist())
print(f"Ready! {len(df)} questions loaded.")


def retrieve_relevant_questions(student_query, top_k=3):
    """
    Standard retrieval — find top_k most semantically similar
    questions regardless of difficulty.
    """
    query_embedding = model.encode([student_query])
    scores = cosine_similarity(query_embedding, question_embeddings)[0]
    top_indices = scores.argsort()[-top_k:][::-1]
    return df.iloc[top_indices][
        ['question', 'mark_scheme_answer', 'topic', 'difficulty', 'marks']
    ].to_dict('records')


def get_grade_appropriate_difficulties(grade):
    """
    Map student grade to appropriate difficulty levels.

    Grade 3 and below : easy only
    Grade 4            : easy only
    Grade 5            : easy + medium
    Grade 6            : medium + hard
    Grade 7+           : all difficulties
    """
    if grade <= 4:
        return ["easy"]
    elif grade == 5:
        return ["easy", "medium"]
    elif grade == 6:
        return ["medium", "hard"]
    else:
        return ["easy", "medium", "hard"]


def retrieve_relevant_questions_filtered(student_query, grade, top_k=3):
    """
    Difficulty-filtered RAG — constrain the candidate pool to
    grade-appropriate questions before ranking by cosine similarity.

    This ensures a Grade 3 student is never served a 6-mark evaluate
    question, and a Grade 6 student is not held back by easy recall questions.

    Falls back to unfiltered retrieval if the filtered pool is too small.
    """
    appropriate_difficulties = get_grade_appropriate_difficulties(grade)

    # Filter dataset to grade-appropriate questions only
    filtered_df = df[df['difficulty'].isin(appropriate_difficulties)]

    # Fallback: if filtered pool is too small, use full dataset
    if len(filtered_df) < top_k:
        return retrieve_relevant_questions(student_query, top_k)

    # Get embeddings for filtered questions only
    filtered_indices = filtered_df.index.tolist()
    filtered_embeddings = question_embeddings[filtered_indices]

    # Find most similar within the filtered pool
    query_embedding = model.encode([student_query])
    scores = cosine_similarity(query_embedding, filtered_embeddings)[0]
    top_local_indices = scores.argsort()[-top_k:][::-1]

    # Map back to original dataframe indices
    top_global_indices = [filtered_indices[i] for i in top_local_indices]
    return df.iloc[top_global_indices][
        ['question', 'mark_scheme_answer', 'topic', 'difficulty', 'marks']
    ].to_dict('records')


def detect_topic(query):
    """
    Detect which AQA topic a query most likely belongs to
    by finding the closest matching question in the dataset.
    """
    results = retrieve_relevant_questions(query, top_k=1)
    return results[0]['topic'] if results else None


#  Test 

if __name__ == "__main__":
    print("\n── Standard retrieval ──")
    results = retrieve_relevant_questions("what happens during mitosis?")
    for r in results:
        print(f"  [{r['difficulty']}] {r['question'][:60]}")

    print("\n── Filtered retrieval Grade 3 (easy only) ──")
    results = retrieve_relevant_questions_filtered(
        "what happens during mitosis?", grade=3
    )
    for r in results:
        print(f"  [{r['difficulty']}] {r['question'][:60]}")

    print("\n── Filtered retrieval Grade 5 (easy + medium) ──")
    results = retrieve_relevant_questions_filtered(
        "what happens during mitosis?", grade=5
    )
    for r in results:
        print(f"  [{r['difficulty']}] {r['question'][:60]}")

    print("\n── Filtered retrieval Grade 6 (medium + hard) ──")
    results = retrieve_relevant_questions_filtered(
        "what happens during mitosis?", grade=6
    )
    for r in results:
        print(f"  [{r['difficulty']}] {r['question'][:60]}")

    print(f"\nDetected topic: {detect_topic('what happens during mitosis?')}")
