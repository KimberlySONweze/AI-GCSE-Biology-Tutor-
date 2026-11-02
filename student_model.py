STUDENT_PROFILES = {
    "alex": {
        "name": "Alex",
        "gender": "not specified",
        "age": 15,
        "grade": 5,
        "weak_topics": ["Cell Biology", "Photosynthesis & Respiration"],
        "strong_topics": ["Ecology"],
        "learning_preference": "Benefits from short hints and step-by-step breakdown",
        "common_errors": "Confuses mitosis and meiosis, struggles to explain processes sequentially",
        "session_history": "Previously confused mitosis and meiosis in two separate questions",
        "recommended_topic": "Cell Biology",
        "scaffolding_level": "high"
    },
    "jordan": {
        "name": "Jordan",
        "gender": "not specified",
        "age": 14,
        "grade": 6,
        "weak_topics": ["Infection & Response"],
        "strong_topics": ["Photosynthesis & Respiration", "Genetics & Evolution"],
        "learning_preference": "Benefits from worked examples and breaking knowledge into smaller steps",
        "common_errors": "Does not use key terms effectively, answers too vague",
        "session_history": "Scored partially on three Infection & Response questions due to missing vocabulary",
        "recommended_topic": "Infection & Response",
        "scaffolding_level": "medium"
    },
    "sam": {
        "name": "Sam",
        "gender": "not specified",
        "age": 16,
        "grade": 3,
        "weak_topics": ["Cell Biology", "Genetics & Evolution",
                        "Homeostasis", "Infection & Response",
                        "Photosynthesis & Respiration", "Ecology"],
        "strong_topics": [],
        "learning_preference": "Strong visual learner — understands processes much better when shown as flow diagrams with arrows rather than paragraphs of text",
        "common_errors": "Struggles significantly with all written explanations, cannot retain sequences of steps when given as text, very low confidence",
        "session_history": "Has attempted questions across multiple topics and scored poorly on all. Responds much better to visual representations.",
        "recommended_topic": "Cell Biology",
        "scaffolding_level": "very high"
    },
    "priya": {
        "name": "Priya",
        "gender": "female",
        "age": 15,
        "grade": 6,
        "weak_topics": ["Genetics & Evolution", "Homeostasis"],
        "strong_topics": ["Cell Biology", "Infection & Response"],
        "learning_preference": "Confident and analytical, prefers to understand the 'why' behind processes rather than memorising steps",
        "common_errors": "Rushes evaluation questions, does not fully consider both sides of an argument",
        "session_history": "Performed well on Cell Biology questions but lost marks on 6-mark evaluate questions across all topics",
        "recommended_topic": "Genetics & Evolution",
        "scaffolding_level": "low"
    },
    "marcus": {
        "name": "Marcus",
        "gender": "male",
        "age": 15,
        "grade": 6,
        "weak_topics": ["Homeostasis", "Photosynthesis & Respiration", "Ecology"],
        "strong_topics": ["Infection & Response"],
        "learning_preference": "Responds well to real-world analogies and connections to everyday life, disengages with abstract explanations",
        "common_errors": "Struggles to use scientific terminology, writes answers in everyday language rather than using key terms",
        "session_history": "Has shown good understanding of pathogens contextually but cannot reproduce formal definitions under exam conditions",
        "recommended_topic": "Homeostasis",
        "scaffolding_level": "high"
    }
}


class StudentModel:
    def __init__(self, student_id):
        self.profile = STUDENT_PROFILES[student_id]
        self.student_id = student_id
        self.name = self.profile["name"]
        self.gender = self.profile["gender"]

        # Session tracking
        self.topics_covered = []
        self.weak_topics = self.profile["weak_topics"].copy()
        self.current_topic = None          # tracks the topic being explored right now
        self.questions_on_current_topic = 0  # how many questions asked on current topic
        self.topic_scores = {}             # stores TF-IDF assessment scores per topic
        self.correct_count = 0
        self.incorrect_count = 0

    def update(self, topic, understood, score=None):
        """Update student model after each interaction."""
        # Track topic coverage
        if topic not in self.topics_covered:
            self.topics_covered.append(topic)

        # Store assessment score if provided
        if score is not None:
            if topic not in self.topic_scores:
                self.topic_scores[topic] = []
            self.topic_scores[topic].append(score)

        # Update performance counts
        if understood:
            self.correct_count += 1
            if topic in self.weak_topics:
                self.weak_topics.remove(topic)
        else:
            self.incorrect_count += 1
            if topic not in self.weak_topics:
                self.weak_topics.append(topic)

        # Update current topic tracking
        if self.current_topic == topic:
            self.questions_on_current_topic += 1
        else:
            self.current_topic = topic
            self.questions_on_current_topic = 1

    def set_current_topic(self, topic):
        """Set the current topic being explored."""
        if self.current_topic != topic:
            self.current_topic = topic
            self.questions_on_current_topic = 0

    def recommend_next_topic(self):
        """
        Recommend next topic based on:
        1. Weak topics not yet attempted this session
        2. Topics with lowest average TF-IDF assessment score
        3. Untouched topics
        """
        all_topics = [
            "Cell Biology",
            "Infection & Response",
            "Photosynthesis & Respiration",
            "Homeostasis",
            "Genetics & Evolution",
            "Ecology"
        ]

        # Priority 1: weak topics not yet covered this session
        for topic in all_topics:
            if topic in self.weak_topics and topic not in self.topics_covered:
                return f"{topic} (flagged as weak area)"

        # Priority 2: topics with lowest average assessment score
        if self.topic_scores:
            avg_scores = {
                t: sum(s) / len(s)
                for t, s in self.topic_scores.items() if s
            }
            if avg_scores:
                worst = min(avg_scores, key=avg_scores.get)
                if avg_scores[worst] < 0.5:
                    return f"{worst} (low assessment score: {avg_scores[worst]:.0%})"

        # Priority 3: any topic not yet covered
        for topic in all_topics:
            if topic not in self.topics_covered:
                return topic

        return "Revision — all topics covered this session!"

    def get_profile_summary(self):
        """Returns formatted student profile for injection into system prompt."""
        weak = ', '.join(self.weak_topics) if self.weak_topics else "None identified"
        strong = ', '.join(self.profile['strong_topics']) if self.profile['strong_topics'] else "None identified"

        # Build score summary if any scores exist
        score_summary = ""
        if self.topic_scores:
            parts = []
            for topic, scores in self.topic_scores.items():
                avg = sum(scores) / len(scores)
                parts.append(f"{topic}: {avg:.0%}")
            score_summary = f"\nAssessment Scores This Session: {', '.join(parts)}"

        return f"""Name: {self.name}
Gender: {self.gender}
Age: {self.profile['age']}, Year {11 if self.profile['grade'] >= 6 else 10}
Current Grade: {self.profile['grade']}
Weak Topics: {weak}
Strong Topics: {strong}
Learning Preference: {self.profile['learning_preference']}
Common Errors: {self.profile['common_errors']}
Session History: {self.profile['session_history']}
Current Topic Being Explored: {self.current_topic or 'Not yet set'}
Questions Asked on Current Topic: {self.questions_on_current_topic}
Recommended Next Topic: {self.recommend_next_topic()}
Scaffolding Level: {self.profile['scaffolding_level']}{score_summary}""".strip()


# Test 
if __name__ == "__main__":
    print("Testing all 5 student profiles...\n")
    for sid in ["alex", "jordan", "sam", "priya", "marcus"]:
        student = StudentModel(sid)
        print(f"=== {student.name.upper()} ===")
        print(student.get_profile_summary())
        print()
