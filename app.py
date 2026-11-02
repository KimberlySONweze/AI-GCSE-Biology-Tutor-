import streamlit as st
from tutor import get_tutor_response
from student_model import StudentModel
from assessment import assess_answer

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="GCSE Biology AI Tutor",
    page_icon="🧬",
    layout="wide"
)

st.title(" GCSE Biology AI Tutor")
st.caption("AQA GCSE Biology — Intelligent Tutoring System Prototype")

# ── Sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.title("Student Profile")

student_options = {
    "alex":   "Alex   — Grade 5",
    "jordan": "Jordan — Grade 6",
    "sam":    "Sam    — Grade 3",
    "priya":  "Priya  — Grade 6 (F)",
    "marcus": "Marcus — Grade 4 (M)",
}

student_choice = st.sidebar.selectbox(
    "Select student:",
    list(student_options.keys()),
    format_func=lambda x: student_options[x]
)

# ── Session state — reset when student changes ────────────────────────────────

if ("student_id" not in st.session_state
        or st.session_state.student_id != student_choice):
    st.session_state.student = StudentModel(student_choice)
    st.session_state.student_id = student_choice
    st.session_state.history = []
    st.session_state.messages = []
    st.session_state.last_assessment = None

student = st.session_state.student

# ── Sidebar — profile info ────────────────────────────────────────────────────

st.sidebar.markdown("---")
st.sidebar.markdown("Active Profile:")
st.sidebar.text(student.get_profile_summary())

st.sidebar.markdown("---")
st.sidebar.markdown("Recommended Next Topic:")
st.sidebar.info(student.recommend_next_topic())

if student.current_topic:
    st.sidebar.markdown(" Current Topic:")
    st.sidebar.success(
        f"{student.current_topic} "
        f"({student.questions_on_current_topic} question(s) asked)"
    )

# ── Sidebar — TF-IDF assessment display ──────────────────────────────────────

def render_tfidf_sidebar(assessment):
    """
    Render TF-IDF assessment results in the sidebar after each student answer.
    Shows score, which AQA key terms were used and which were missed.
    """
    if not assessment:
        return

    score   = assessment["score"]
    found   = assessment["found"]
    missing = assessment["missing"]
    question = assessment["question"]

    st.sidebar.markdown("---")
    st.sidebar.markdown("Last Answer — AQA Term Check:")
    st.sidebar.caption(f"Against: {question[:55]}...")

    # Progress bar with colour label
    if score is not None:
        label = (
            "Strong " if score >= 0.7
            else "Partial " if score >= 0.4
            else "Needs work "
        )
        st.sidebar.progress(score, text=f"{label} — {score:.0%} key terms used")

    # Terms the student used
    if found:
        st.sidebar.markdown("Terms used:")
        st.sidebar.markdown(" ".join([f"`{t}`" for t in found]))

    # Terms the student missed
    if missing:
        st.sidebar.markdown("Terms missed:")
        st.sidebar.markdown(" ".join([f"`{t}`" for t in missing]))
        st.sidebar.caption(
            "These terms appear in the AQA mark scheme — "
            "try to include them in your next answer."
        )

# ── Sidebar — topic score history ────────────────────────────────────────────

if student.topic_scores:
    st.sidebar.markdown("---")
    st.sidebar.markdown("Session Assessment Scores:")
    for topic, scores in student.topic_scores.items():
        avg = sum(scores) / len(scores)
        st.sidebar.progress(avg, text=f"{topic}: {avg:.0%}")

# ── Sidebar — practice questions ─────────────────────────────────────────────

st.sidebar.markdown("---")
st.sidebar.markdown(" Suggested Practice Questions:")

if student.current_topic:
    from retrieval import retrieve_relevant_questions_filtered
    suggestions = retrieve_relevant_questions_filtered(
        student.current_topic,
        student.profile["grade"],
        top_k=3
    )
    for i, s in enumerate(suggestions, 1):
        with st.sidebar.expander(
            f"{i}. {s['difficulty'].title()} — click to expand"
        ):
            st.write(f"Question: {s['question']}")
            st.caption(f"Topic: {s['topic']} | Marks: {s.get('marks', '?')}")
            if st.button(f"Practice this", key=f"practice_{i}"):
                st.session_state.messages.append({
                    "role": "user", "content": s['question']
                })
                resp = get_tutor_response(
                    s['question'],
                    st.session_state.student,
                    st.session_state.history
                )
                st.session_state.messages.append({
                    "role": "assistant", "content": resp
                })
                st.session_state.history.append({
                    "role": "user", "content": s['question']
                })
                st.session_state.history.append({
                    "role": "assistant", "content": resp
                })
                st.rerun()

# ── Main chat area ────────────────────────────────────────────────────────────

st.markdown(
    f" Hello! I am your GCSE Biology tutor. "
    f"Working with **{student.name}** today "
    f"(Grade {student.profile['grade']}, "
    f"scaffolding level: {student.profile['scaffolding_level']})."
)
st.markdown("Ask me anything about AQA GCSE Biology!")
st.markdown("---")

# Render last TF-IDF result in sidebar
render_tfidf_sidebar(st.session_state.last_assessment)

# Display existing messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# ── Chat input ────────────────────────────────────────────────────────────────

user_input = st.chat_input("Type your biology question here...")

if user_input:
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # TF-IDF assessment on student's answer (only if >5 words)
    if len(user_input.split()) > 5:
        from retrieval import retrieve_relevant_questions_filtered
        retrieved = retrieve_relevant_questions_filtered(
            user_input, student.profile["grade"], top_k=1
        )
        if retrieved:
            score, missing, found = assess_answer(
                user_input, retrieved[0]["question"]
            )
            if score is not None:
                st.session_state.last_assessment = {
                    "score":    score,
                    "found":    found,
                    "missing":  missing,
                    "question": retrieved[0]["question"]
                }
                student.update(
                    retrieved[0]["topic"],
                    understood=(score >= 0.5),
                    score=score
                )

    # Get tutor response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_tutor_response(
                user_input,
                st.session_state.student,
                st.session_state.history
            )
        st.write(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.session_state.history.append({"role": "user",      "content": user_input})
    st.session_state.history.append({"role": "assistant", "content": response})

    st.rerun()
