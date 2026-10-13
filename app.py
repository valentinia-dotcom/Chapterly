"""Chapterly: one-command Streamlit starter for IIT Mandi Track D."""
from __future__ import annotations

import statistics
from pathlib import Path

import pandas as pd
import streamlit as st
from html import escape

from ai import (answer_question, describe_diagram,gemini_key, generate_quiz, generate_mind_map, generate_learning_path)

from mindmaps import render_mindmap
from tutoring import (LEVELS, missed_questions, needs_tutor_invite, next_level,
                      quiz_percentage, retry_missed_quiz, review_payload)
from core import (BASE_DIR, activity, add_diagram_document, add_document, add_url_document, difficulty_for,
                  get_document_topics, get_documents, init_db, mastery, retrieve,
                  save_attempt, topic_stats, web_source_url, get_chunks, get_learning_path, save_learning_path,
                  complete_learning_topic)

st.set_page_config(page_title="Chapterly", page_icon="📚", layout="wide",
                   initial_sidebar_state="expanded")
init_db()

# Navigation is applied on the NEXT rerun, before the radio widget exists.
# Streamlit does not allow changing a widget-backed key after it renders.
if "nav_request" in st.session_state:
    st.session_state["workspace"] = st.session_state.pop("nav_request")

st.markdown("""
<style>
.block-container {padding-top: 2rem; max-width: 1180px;}
h1, h2, h3 {letter-spacing: -0.025em;}
.hero {border-radius: 20px; padding: 28px 32px; background: linear-gradient(115deg,#252866,#6266db);
       color: white; margin-bottom: 18px;}
.hero h1 {color:white; font-size: 2.25rem; margin:0 0 7px 0;}
.hero p {color:#e8e8ff; margin-bottom:0;}
.tag {display:inline-block; padding:5px 10px; border-radius:16px; background:#ebebff;
      color:#3437a3; font-size:0.82rem; font-weight:700; margin-bottom:12px;}
.muted {color:#606b83; font-size:.93rem;}

/* Dashboard metric cards */
div[data-testid="stMetric"] {
    background-color: #1B2A4A;
    padding: 22px;
    border-radius: 14px;
    border: 1px solid #34476C;
}

/* Metric labels */
div[data-testid="stMetricLabel"] {
    color: #A9B1C5;
}

/* Metric values */
div[data-testid="stMetricValue"] {
    color: #FFFFFF;
}

/* Dashboard welcome banner */
.hero {
    background: linear-gradient(115deg, #1B2A4A, #30356B);
    border: 1px solid #30374A;
    border-radius: 16px;
    padding: 28px;
}

/* Main content spacing */
.block-container {
    max-width: 1180px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Softer dividers */
hr {
    border-color: #30374A;
}

/* Learning progress cards */
.learning-card {
    background: #1B2A4A;
    border: 1px solid #34476C;
    border-radius: 14px;
    padding: 22px;
    margin: 16px 0;
}

.section-heading {
    color: #FFFFFF;
    font-size: 1.15rem;
    font-weight: 600;
    margin-bottom: 20px;
}

.topic-row {
    margin-bottom: 18px;
}

.topic-meta {
    display: flex;
    justify-content: space-between;
    color: #E7EAF5;
    font-size: 0.95rem;
    margin-bottom: 9px;
}

.topic-bar {
    height: 9px;
    background: #34476C;
    border-radius: 20px;
    overflow: hidden;
}

.topic-bar-fill {
    height: 100%;
    border-radius: 20px;
}

.recommendation-text {
    color: #CBD5E8;
    font-size: 0.95rem;
    line-height: 1.6;
}

</style>

""", unsafe_allow_html=True)

with st.sidebar:
    st.title("📚 Chapterly")
    page = st.radio("Workspace", ["🏠 Dashboard", "📁 Learning Library", "💬 AI Tutor", "🧠 Adaptive Quiz",
        "🗺️ Mind Maps"],
    label_visibility="collapsed",
    key="workspace")

    st.divider()
    if gemini_key():
        st.success("Gemini connected")
    else:
        st.info("Offline preview mode")
        st.caption("Set GEMINI_API_KEY in your .env file for AI explanations and questions.")


def load_sample():
    return add_document(path.name, path.read_bytes())
    path = BASE_DIR / "sample_materials" / "photosynthesis.txt"
    return add_document(path.name, path.read_bytes())


def title(title_, description):
    st.title(title_)
    st.caption(description)


def dashboard():
    # Chapterly welcome section
    st.markdown("""
    <div class="hero">
        <h1>Chapterly</h1>
        <p>Your space to learn, practice, and improve.</p>
    </div>
    """, unsafe_allow_html=True)

    # Get existing student data
    documents = get_documents()
    stats = topic_stats()
    history = activity()

    # Dashboard statistics
    metrics = [
        ("Study Materials", len(documents)),
        ("Questions Attempted", len(history) if len(history) < 50 else "50+"),
        ("Indexed Passages", sum(d["passages"] for d in documents)),
        (
            "Average Mastery",
            f"{round(statistics.mean(s['mastery'] for s in stats))}%"
            if stats else "—"
        )
    ]

    # Compact two-column metric layout
    cols = st.columns(4, gap="small")

    for col, (label, value) in zip(cols, metrics):
        with col:
            st.metric(label, value)

    st.divider()

    # Empty library
    if not documents:
        st.subheader("Start with a sample lesson")
        st.write(
            "Explore Chapterly with a short lesson, "
            "or upload your own study materials."
        )

        if st.button("✨ Load sample lesson", type="primary"):
            result = load_sample()
            st.success(result["message"])
            st.rerun()

        return

    # Learning progress
    st.subheader("Your learning journey")

    if stats:
        bars = ""

        for item in sorted(stats, key=lambda x: x["topic"].lower()):
            name = escape(str(item["topic"]).title())
            score = max(0, min(100, round(float(item["mastery"]))))

            if score < 40:
                color = "#D6A36B"
            elif score < 60:
                color = "#A78BFA"
            else:
                color = "#6489F5"

            bars += f"""
            <div class="topic-row">
                <div class="topic-meta">
                    <span>{name}</span>
                    <span>{score}%</span>
                </div>
                <div class="topic-bar">
                    <div class="topic-bar-fill"
                         style="width:{score}%; background:{color};">
                    </div>
                </div>
            </div>
            """

        st.html(
    '<div class="learning-card">'
    '<div class="section-heading">Learning Progress</div>'
    + bars +
    '</div>'
)

    else:
        st.info("Take your first quiz to see your learning progress.")

    # One personalized recommendation
    weak = sorted(
        [s for s in stats if s["mastery"] < 60],
        key=lambda x: x["mastery"]
    )

    if weak:
        topics = ", ".join(
            s["topic"].title() for s in weak[:2]
        )

        recommendation = (
            f"Focus on {topics}. Review these topics with "
            "your AI Tutor before your next quiz."
        )

    elif stats:
        recommendation = (
            "Great progress! Continue practicing or try "
            "a more challenging quiz."
        )

    else:
        recommendation = (
            "Ask your AI Tutor a question or take "
            "a quiz to begin tracking your progress."
        )

    st.markdown(f"""
    <div class="learning-card">
        <div class="section-heading">Suggested next step</div>
        <div class="recommendation-text">
            {escape(recommendation)}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Keep recent materials available without cluttering the dashboard
    with st.expander("Recently added materials"):
        for document in documents[:5]:
            st.write(
                f"📄 **{document['name']}** — "
                f"{document['passages']} passages"
            )



def library():
    title("Learning Library",
    "Keep your notes, slides, and lectures in one place.")
    left, right = st.columns([2, 1], gap="large")
    with left:
        files = st.file_uploader("Choose learning materials", type=["pdf", "pptx", "txt", "md", "mp4", "mp3", "wav", "m4a"],
                                 accept_multiple_files=True,
                                 help="Extracts PDF pages, PPT slides and timestamps from transcribed media.")
        if st.button("Add to library", type="primary", disabled=not files):
            for file in files or []:
                with st.spinner(f"Processing {file.name}..."):
                    try:
                        result = add_document(file.name, file.getvalue())
                        (st.success if result["added"] else st.info)(f"{file.name}: {result['message']}")
                    except Exception as exc:
                        st.error(f"{file.name}: {exc}")
        with st.expander("🖼️ Add a diagram", expanded=False):
            st.caption(
             "When you click Analyze and add diagram, the image is sent to Google Gemini "
             "to create a searchable study description. Upload only images you are allowed to share."
            )
            diagram = st.file_uploader(
                "Choose a diagram image",
                 type=["png", "jpg", "jpeg", "webp"],
                 accept_multiple_files=False,
                 help="Supported formats: PNG, JPG, JPEG, and WebP. Maximum size: 8 MB.",
                 key="diagram_uploader",
            )
            if diagram:
                st.image(diagram, caption=diagram.name, use_container_width=True)
            if st.button(
                "Analyze and add diagram",
                type="primary",
                disabled=not diagram or not gemini_key(),
            ):
                with st.spinner("Asking Gemini to describe the diagram..."):
                    try:
                        image_data = diagram.getvalue()
                        description = describe_diagram(diagram.name, image_data)
                        result = add_diagram_document(diagram.name, image_data, description)
                        if result["added"]:
                            st.success(result["message"])
                            with st.expander("Preview generated description"):
                                st.write(description)
                        else:
                            st.info(result["message"])
                    except Exception as exc:
                        st.error(f"Could not analyze diagram: {exc}")
            if not gemini_key():
                st.info("Add a Gemini API key to analyze images. Uploaded images are not sent while offline.")
        
        with st.expander("🌐 Import from website", expanded=False):

            page_url = st.text_input(
                "Web page URL",
                placeholder="https://example.com/lesson",
                help="Add a public learning page to your library."
            )

            if st.button(
                "Add website to library",
                type="primary",
                disabled=not page_url.strip()
            ):
                with st.spinner("Adding learning material..."):
                    try:
                        result = add_url_document(page_url.strip())

                        if result["added"]:
                            st.success(result["message"])
                        else:
                            st.info(result["message"])

                    except Exception as exc:
                        st.error(f"Could not import web page: {exc}")

    with right:
        st.markdown("**Quick start**")
        st.write("No study material handy? Load a sample biology lesson.")
        if st.button("Load demo lesson"):
            result = load_sample()
            (st.success if result["added"] else st.info)(result["message"])
        st.info("Video and audio files may take a little longer to process.")
    st.divider()
    st.subheader("Your Materials")
    docs = get_documents()
    if not docs:
        st.caption("No sources uploaded yet.")
    for d in docs:
        with st.expander(f"📘 {d['name']} · {d['passages']} passages"):
            st.write(f"Type: {d['kind'].upper()}")
            st.write(f"Imported: {d['uploaded_at'][:19]} UTC")
            st.caption("Retrieved answers will show precise page, slide or timestamp locations.")

            # Smart Learning Path
            st.divider()
            path = get_learning_path(d["id"])

            if not path:
                if st.button(
                    "✨ Generate Learning Path",
                    key=f"generate_path_{d['id']}"                ):
                    with st.spinner("Identifying learning topics..."):
                        try:
                            topics = generate_learning_path(d["id"])
                            save_learning_path(d["id"], topics)
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Learning path failed: {exc}")

            else:
                st.markdown("**Your Learning Path**")
                completed = sum(
                    1 for item in path if item["completed"])

                st.progress(completed / len(path),
                    text=f"{completed}/{len(path)} topics completed"                )

                for item in path:
                    icon = "✅" if item["completed"] else "⭕"
                    st.write(
                        f"{icon} {item['topic_order']}. "
                        f"{item['topic_name']}")

                next_topic = next(
                    (item for item in path if not item["completed"]),
                    None
                )

                if next_topic:
                    st.info(
                        f"📚 Up next: {next_topic['topic_name']}"
                    )
                else:
                    st.success("All topics completed!")


def begin_tutoring(question: str, *, topic: str | None = None, review: dict | None = None):
    """Start or restart a teaching journey only after the first response succeeds."""
    answer, passages = answer_question(question, level=1, review=review)
    old = st.session_state.get("tutor_flow")
    
    # Do not start tutoring if no relevant material was found
    if not passages:
        st.session_state.pop("tutor_flow", None)

        raise ValueError(
            "I couldn't find this topic in your study materials. "
            "Please check the spelling, ask a different question, "
            "or upload a relevant lesson."
        )

    if old:
        st.session_state.setdefault("tutor_archive", []).append(old)
    st.session_state.tutor_flow = {
        "question": question,
        "topic": topic or question,
        "review": review,
        "steps": [{"level": 1, "answer": answer, "sources": passages}],
        "understood": False,
    }


def continue_tutoring(level: int, confusion: str = ""):
    """Advance after the API succeeds so an error never discards progress."""
    flow = st.session_state.tutor_flow
    answer, passages = answer_question(flow["question"], level=level, review=flow["review"],
                                       confusion=confusion)
    flow["steps"].append({"level": level, "answer": answer, "sources": passages,
                          "confusion": confusion})


def tutor():
    title("AI Tutor", "Learn at your pace: definition → simpler words → real-world example → explain like I'm 10.")
    st.caption(
        f"DEBUG next lesson: {st.session_state.get('tutor_pending')}"
    )
    if not get_documents():
        st.warning("First add a study material in the Learning Library.")
        return

    # Handle a student's explicit request for tutoring after a low-scoring quiz.
    pending = st.session_state.get("tutor_pending")
    if pending:
        with st.spinner("Preparing a lesson on your missed question..."):
            try:
                begin_tutoring(pending["question"], topic=pending["topic"], review=pending["review"])
                del st.session_state["tutor_pending"]
            except Exception as exc:
                st.error(f"Could not start this tutoring session: {exc}")
                return

    if not gemini_key():
        st.info("Offline preview: source excerpts work, but different explanation levels require GEMINI_API_KEY in .env.")

    flow = st.session_state.get("tutor_flow")
    if flow:
        if flow["review"]:
            st.info(f"📘 Quiz recovery lesson for **{flow['review']['topic'].title()}**: we'll work through the question you missed.")
        with st.chat_message("user"):
            st.markdown(flow["question"])

        for idx, step in enumerate(flow["steps"]):
            label = LEVELS[step["level"]]
            if step.get("confusion"):
                st.caption(f"You said you were confused about: {step['confusion']}")
            with st.chat_message("assistant"):
                st.markdown(f"**Level {step['level']} of 4 — {label}**")
                st.markdown(step["answer"])
                if step["sources"]:
                    with st.expander("View cited source passages"):
                        for p in step["sources"]:
                            st.markdown(f"**[{p['marker']}] {p['source']}**")
                            url = web_source_url(p["source"])
                            if url:
                                st.link_button("Open original web page", url,
                                               key=f"tutor-source-{idx}-{p['marker']}")
                            st.caption(p["content"])

        if not flow["understood"]:
            level = flow["steps"][-1]["level"]
            st.markdown("#### Did you understand this explanation?")
            if level < 4:
                yes, no = st.columns(2)
                with yes:
                    if st.button("✅ Yes, I understood", type="primary", use_container_width=True):
                        flow["understood"] = True
                        st.rerun()
                with no:
                    if st.button("🔄 Not yet — explain differently", use_container_width=True,
                                 disabled=not bool(gemini_key())):
                        with st.spinner(f"Preparing level {next_level(level)}..."):
                            try:
                                continue_tutoring(next_level(level))
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Could not prepare another explanation: {exc}")
            else:
                st.caption("Still unsure? Tell me what is confusing, and I'll explain that exact part in smaller steps.")
                confusion = st.text_input("Which part feels confusing?", key="tutor_confusion",
                                          placeholder="For example: Why do plants need light?")
                left, right = st.columns(2)
                with left:
                    if st.button("✅ I understand now", type="primary", use_container_width=True):
                        flow["understood"] = True
                        st.rerun()
                with right:
                    if st.button("🧩 Teach this part step by step", use_container_width=True,
                                 disabled=not bool(gemini_key()) or not confusion.strip()):
                        with st.spinner("Explaining your specific confusion..."):
                            try:
                                continue_tutoring(4, confusion=confusion)
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Could not explain that part: {exc}")
        else:
            st.success("Great — you've completed this explanation! Try a short quiz to check what you learned.")
            if st.button("🧠 Check my learning with a quiz", type="primary"):
                st.session_state.quiz = None
                st.session_state.nav_request = "🧠 Adaptive Quiz"
                st.rerun()

    previous = st.session_state.get("tutor_archive", [])
    if previous:
        with st.expander(f"Previous tutor topics ({len(previous)})"):
            for session in reversed(previous[-8:]):
                st.markdown(f"**{session['question']}** — {len(session['steps'])} explanation(s)")

    question = st.chat_input("Ask a question about your uploaded lesson...")
    if question and question.strip():
        with st.spinner("Finding evidence and preparing a clear definition..."):
            try:
                begin_tutoring(question.strip(), topic=question.strip())
                st.rerun()
            except Exception as exc:
                st.error(f"Could not answer: {exc}")

    if not flow:
        st.info("Type a question below. I'll begin with a clear definition and detailed explanation.")


def mind_maps():
    st.title("Mind Maps")
    st.caption("Turn your lessons into visual concept maps.")

    documents = get_documents()

    if not documents:
        st.info("Add a learning material to get started.")
        return

    # Choose a source
    selected_id = st.selectbox(
        "Choose study material",
        options=[doc["id"] for doc in documents],
        format_func=lambda doc_id: next(
            doc["name"]
            for doc in documents
            if doc["id"] == doc_id
        )
    )

    selected_doc = next(
        doc for doc in documents
        if doc["id"] == selected_id
    )

    topic = st.text_input(
        "Focus on a topic (optional)",
        placeholder="e.g. Photosynthesis"
    )

    if st.button("Generate Mind Map", type="primary"):

        with st.spinner("Creating your mind map..."):
            try:
                # Find passages belonging to this document
                all_chunks = [
                    chunk for chunk in get_chunks()
                    if (
                        chunk.get("document_id") == selected_id
                        or chunk.get("name") == selected_doc["name"]
                    )
                ]

                if topic.strip():
                    passages = retrieve(
                        topic.strip(),
                        10,
                        document_id=selected_id
                    )
                else:
                    # Sample passages across the document
                    step = max(1, (len(all_chunks) + 9) // 10)
                    passages = all_chunks[::step][:10]

                if not passages:
                    st.warning(
                        "No relevant passages found. "
                        "Try another topic or material."
                    )
                else:
                    tree = generate_mind_map(
                        passages,
                        topic
                    )

                    st.session_state["mind_map_result"] = {
                        "document_id": selected_id,
                        "tree": tree,
                        "passages": passages
                    }

                    st.success("Mind map generated!")

            except Exception as exc:
                st.error(f"Could not generate mind map: {exc}")

    # Display generated map
    result = st.session_state.get("mind_map_result")

    if result and result["document_id"] == selected_id:
        st.subheader(result["tree"]["root"])

        diagram = render_mindmap(result["tree"])

        st.download_button(
            "Download Mind Map",
            data=diagram,
            file_name="chapterly_mindmap.mmd",
            mime="text/plain"
        )

        with st.expander("View source passages"):
            for passage in result["passages"]:
                st.markdown(f"**{passage['source']}**")
                st.caption(passage["content"][:400])

def quiz():
    title("Adaptive Quiz", "Choose a study material and one of its suggested topics.")
    documents = get_documents()
    if not documents:
        st.warning("Add a learning material in the Library first.")
        return
    
    # Automatically select the topic from Continue Learning
    target = st.session_state.pop("next_quiz_target", None)

    if target and any(
        d["id"] == target["document_id"] for d in documents
    ):
        doc_id = target["document_id"]
        st.session_state["quiz_document_id"] = doc_id
        st.session_state[f"quiz_topic_{doc_id}"] = target["topic"]

    st.caption("Your mastery suggests a starting difficulty, but you can choose any level.")
    selected_document_id = st.selectbox(
        "Choose study material",
        options=[document["id"] for document in documents],
        format_func=lambda document_id: next(
            document["name"] for document in documents if document["id"] == document_id
        ),
        key="quiz_document_id",
        help="Topics are suggested from the text extracted from this source.",
    )
    
    # Prefer topics from the saved Smart Learning Path
    learning_path = get_learning_path(selected_document_id)

    if learning_path:
        topics = [item["topic_name"] for item in learning_path]
    else:
        topics = get_document_topics(selected_document_id) or ["General review"]

    topic = st.selectbox(
        "Choose a topic",
        options=topics,
        key=f"quiz_topic_{selected_document_id}",
        help="These topic suggestions are extracted from the selected material.",
    )
    with st.expander(f"Preview passages for {topic}"):
        previews = retrieve(topic, 4, document_id=selected_document_id)
        if previews:
            for index, passage in enumerate(previews):
                st.markdown(f"**{passage['source']}**")
                url = web_source_url(passage["source"])
                if url:
                    st.link_button(
                        "Open original web page", url,
                        key=f"preview-source-{selected_document_id}-{index}",
                    )
                st.write(passage["content"])
        else:
            st.info("No exact topic match was found; the quiz will use passages from the selected material.")
    left, right = st.columns([1, 2], vertical_alignment="bottom")
    recommended_level = difficulty_for(topic) if topic.strip() else "medium"
    with left:
        st.metric("Current topic mastery", f"{mastery(topic)}%" if topic.strip() else "—")
    with right:
        level = st.selectbox(
            "Choose difficulty",
            options=["easy", "medium", "hard"],
            index=["easy", "medium", "hard"].index(recommended_level),
            format_func=str.title,
            key="quiz_difficulty",
            help=f"Suggested from your current topic mastery: {recommended_level.title()}.",
        )
    if st.button("✨ Generate adaptive quiz", type="primary", disabled=not topic.strip()):
        with st.spinner("Creating source-grounded quiz..."):
            try:
                questions, passages = generate_quiz(
                    topic.strip(), level, count=3, document_id=selected_document_id )
                
                st.session_state.quiz = {"document_id": selected_document_id,
                    "topic": topic.strip(),
                    "level": level,
                    "questions": questions,
                    "sources": passages,
                    "graded": False,
                    "results": [],
                    "is_retry": False,
                    "epoch": st.session_state.get("quiz_epoch", 0) + 1                }

                st.session_state.quiz_epoch = st.session_state.quiz["epoch"]
                st.rerun()
            except Exception as exc:
                st.error(f"Quiz creation failed: {exc}")

    current = st.session_state.get("quiz")
    
    # Clear questions from a different topic or material
    if current and (
        current.get("document_id") != selected_document_id
        or current.get("topic") != topic.strip()
    ):
        st.session_state.quiz = None
        current = None

    if not current:
        st.info("Choose a topic and generate a quiz. Without an API key, basic extractive sample questions are available.")
        return
    st.divider()
    retry_label = " · missed-question retry" if current.get("is_retry") else ""
    st.subheader(f"{current['topic'].title()} · {current['level'].title()} level{retry_label}")
    if not gemini_key():
        st.warning("Offline demo questions are basic sentence completion; use Gemini for adaptive AI-authored questions.")
    questions = current["questions"]
    if not current["graded"]:
        with st.form(f"attempt_{current['epoch']}"):
            for n, q in enumerate(questions):
                st.markdown(f"**Question {n + 1}. {q['question']}**")
                st.radio(f"Answer question {n + 1}", range(4),
                         format_func=lambda idx, opts=q["options"]: opts[idx],
                         index=None, key=f"answer_{current['epoch']}_{n}", label_visibility="collapsed")
            submit = st.form_submit_button("Submit answers", type="primary")
        if submit:
            answers = [st.session_state.get(f"answer_{current['epoch']}_{n}") for n in range(len(questions))]
            if any(idx is None for idx in answers):
                st.error("Please answer all questions before submitting.")
            else:
                results = []
                for q, selected in zip(questions, answers):
                    correct = selected == q["answer_index"]
                    save_attempt(current["topic"], q["question"], q["options"][selected],
                                 correct, current["level"])
                    results.append({"correct": correct, "selected": selected})
                current["graded"] = True
                current["results"] = results
                st.session_state.quiz = current
                st.rerun()
    else:
        score = sum(r["correct"] for r in current["results"])
        
        # SMART LEARNING PATH: complete topic after passing quiz
        passed = (len(questions) > 0
            and score / len(questions) >= 0.60        )

        document_id = current.get("document_id")
        st.caption(
            f"DEBUG: passed={passed}, "
            f"document_id={document_id}, "
            f"topic={current['topic']}, "
            f"is_retry={current.get('is_retry', False)}"
        )

        if passed and document_id is not None and not current.get("is_retry", False):

            learning_path = get_learning_path(document_id)

            topic_exists = any(
                item["topic_name"] == current["topic"]
                for item in learning_path            )

            if topic_exists:
                if not current.get("path_recorded", False):
                    complete_learning_topic(
                        document_id,
                        current["topic"])

                    current["path_recorded"] = True
                    st.session_state.quiz = current

                st.success("✅ Learning Path updated! "
                    "You have completed this topic.")
                
                # Recommend the next unfinished topic
                updated_path = get_learning_path(document_id)

                next_topic = next(
                    (
                        item for item in updated_path
                        if not item["completed"]
                    ),
                    None
                )

                if next_topic:
                    st.info(
                        f"📚 Up next: {next_topic['topic_name']}"
                    )

                    if st.button(
                        "▶ Continue Learning",
                        key=f"continue_learning_{current['epoch']}"
                    ):
                        st.session_state.next_quiz_target = {
                            "document_id": document_id,
                            "topic": next_topic["topic_name"]
                        }

                        st.session_state.tutor_pending = {
                            "question": (
                                f"Explain {next_topic['topic_name']} "
                                "from my learning material."
                            ),
                            "topic": next_topic["topic_name"],
                            "review": None,
                            "document_id": document_id
                        }

                        st.session_state.nav_request = "💬 AI Tutor"
                        st.rerun()

                else:
                    st.success(
                        "🎉 Learning Path Completed! "
                        "You've finished every topic."
                    )


        st.success(f"You scored {score}/{len(questions)} · Updated mastery: {mastery(current['topic'])}%")
        for n, (q, result) in enumerate(zip(questions, current["results"]), 1):
            st.markdown(f"**{n}. {q['question']}**")
            st.write(f"{'✅' if result['correct'] else '❌'} Your answer: {q['options'][result['selected']]}")
            st.write(f"**Correct:** {q['options'][q['answer_index']]}")
            st.info(f"{q['explanation']}  **[{q['source_id']}]**")
        with st.expander("Show evidence for quiz answers"):
            for index, p in enumerate(current["sources"]):
                st.markdown(f"**[{p['marker']}] {p['source']}**")
                url = web_source_url(p["source"])
                if url:
                    st.link_button(
                        "Open original web page", url,
                        key=f"quiz-source-{current['epoch']}-{index}",
                    )
                st.caption(p["content"])
        missed = missed_questions(questions, current["results"])
        if missed:
            if st.button("🔁 Retry missed questions", type="primary"):
                next_epoch = st.session_state.get("quiz_epoch", current["epoch"]) + 1
                st.session_state.quiz = retry_missed_quiz(current, next_epoch)
                st.session_state.quiz_epoch = next_epoch
                st.rerun()
        score_pct = quiz_percentage(score, len(questions))
        if needs_tutor_invite(score, len(questions)):
            if st.session_state.get("review_declined_epoch") != current["epoch"]:
                st.divider()
                st.subheader("📘 Would you like your AI Tutor to help?")
                st.write(f"You scored **{score_pct}%**. Let's review the specific concepts you missed before another quiz.")
                chosen = st.selectbox("Which missed question should we learn first?",
                                      options=range(len(missed)),
                                      format_func=lambda i: f"Question {missed[i][0] + 1}: {missed[i][1]['question']}",
                                      key=f"missed_question_{current['epoch']}")
                yes, no = st.columns(2)
                with yes:
                    if st.button("✅ Yes, teach me", type="primary", use_container_width=True):
                        _, question, result = missed[chosen]
                        try:
                            review = review_payload(current["topic"], question, result, current["sources"])
                            st.session_state.tutor_pending = {
                                "question": f"Help me understand this question: {question['question']}",
                                "topic": current["topic"],
                                "review": review,
                            }
                            st.session_state.nav_request = "💬 AI Tutor"
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Could not prepare tutoring: {exc}")
                with no:
                    if st.button("Not now", use_container_width=True):
                        st.session_state.review_declined_epoch = current["epoch"]
                        st.rerun()
            else:
                st.info("You can return to the AI Tutor anytime to review this topic.")
        elif score_pct < 80:
            st.info("Good work. Review your missed answers and consider asking the AI Tutor before your next quiz.")
        else:
            st.success("Well done! You're ready to try another quiz or a harder topic.")


if page == "🏠 Dashboard":
    dashboard()

elif page == "📁 Learning Library":
    library()

elif page == "💬 AI Tutor":
    tutor()

elif page == "🧠 Adaptive Quiz":
    quiz()

elif page == "🗺️ Mind Maps":
    mind_maps()
