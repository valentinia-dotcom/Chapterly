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
