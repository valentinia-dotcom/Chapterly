# StudyMate AI — Adaptive Teaching Edition (Streamlit)

A minimal, working **Track D: Personalized Tutoring & Adaptive Learning** MVP. Written in Python, with no React, Flask, or n8n.

## Features

- Upload PDFs, PPTX slides, text, and diagram images; import public lesson URLs; optionally audio/video recordings.
- Extract passage-level study material and retain source references (**PDF page**, **slide number**, **media timestamp**, or **diagram image**).
- Build a persistent SQLite learning library with lightweight, typo-tolerant keyword retrieval (RAG). No embedding downloads required.
- **4-stage AI Tutor:** a proper definition and explanation first, then simple language, a real-world analogy, and finally an explanation suitable for a 10-year-old, only when the student asks for it.
- Each stage asks **"Did you understand?"** and moves to the next only when the student selects **Not yet**. At the final level, the student can describe exactly what remains confusing for a more targeted explanation.
- **Quiz → Tutor recovery:** scores below **60%** trigger an optional **"Yes, teach me"** offer. The student can pick a missed question; the tutor receives the exact wrong/correct answers and source evidence and starts with Stage 1.
- After a quiz, students can retry only missed questions; each retry is graded and saved as a new attempt.
- Ask the AI Tutor questions. With a Gemini API key, get generated, passage-grounded answers with citation markers, inspect the supporting excerpts, and open original web-page citations.
- Upload PNG, JPG/JPEG, or WebP diagrams (up to 8 MB) in the Learning Library. Gemini Vision describes visible labels and relationships, and the description becomes searchable/citable study material.
- Select an uploaded material or imported web lesson, choose from topic suggestions extracted from its text, and preview relevant passages before generating a quiz at **easy / medium / hard**. Attempts are graded and saved.
- See topic mastery and get tailored revision recommendations in a Streamlit dashboard.
- Use the included photosynthesis lesson for a rapid demo.

> **Scope:** This is a one-student, hackathon MVP, not a production learning management system. It processes text from PDF/PPTX, readable text from public HTML pages, diagram images analyzed by Gemini, and audio from videos. Scanned-PDF OCR, multi-user accounts, robust evaluation of citation faithfulness, and spaced repetition are future improvements. The simple mastery score is an estimate from recent quiz results, not a validated measure of learning.

## Installation

Requires Python **3.10+** and a terminal. From inside this folder:

```bash
python -m venv .venv
```

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
source .venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
```

Create `.env` by copying `.env.example` and insert your Gemini API key:

```ini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Get a key from [Google AI Studio](https://aistudio.google.com/apikey). Keep it private. The model name may need adjusting to one supported by your account.

Start the UI:

```bash
streamlit run app.py
```

Streamlit will usually open `http://localhost:8501`.

**No Gemini key?** You can still upload materials, view matching excerpts and generate basic fill-in-the-blank demonstration quizzes. **All four explanation styles, their rewording, and AI-authored quizzes require a working Gemini API key.** In offline preview, the **Not yet** and targeted tutoring actions are disabled to avoid presenting source excerpts as generated teaching.

## Optional lecture video / audio transcription

```bash
pip install -r requirements-video.txt
```

Then upload `.mp4`, `.mp3`, `.m4a`, or `.wav` in **Learning Library**. The project uses `faster-whisper` on CPU with the `base` model. The first run downloads model weights and can be slow. For the hackathon, prioritize PDF/PPTX and test video afterward.

To import a lesson from a website, open **Learning Library**, paste its public `https://` URL in **Import a lesson from a web page**, and click **Index web page**. The extracted text becomes a source in the library and can be used by the AI Tutor and Adaptive Quiz. Only readable HTML pages are supported; login-only pages, PDFs linked from a page, and sites that block automated requests cannot be imported. Imports are limited to 2 MB per page.

## 3-minute demo script

1. Open the **Dashboard**, choose **Load sample lesson**.
2. Open **AI Tutor**, ask: *"What does chlorophyll do during photosynthesis?"* Confirm citations show the uploaded source.
3. In AI Tutor, click **Not yet — explain differently** to see the simple explanation, then the real-world example, then the child-friendly explanation. At level 4, type what is still confusing for a new step-by-step explanation.
4. Open **Adaptive Quiz**, topic **photosynthesis**, and intentionally get at least **2 of the 3 answers wrong** (score below 60%). Click **Yes, teach me** and select a missed question. Observe the source-grounded, four-stage tutor handoff.
5. Click **I understand** and **Check my learning with a quiz**. Return to **Dashboard** to see updated mastery.
6. Upload a real PDF, PPTX or lecture recording and repeat with your own content.

## Files

```text
StudyMate_AI_Starter/
├── app.py                    # Streamlit user interface
├── core.py                   # Data extraction, retrieval, SQLite, mastery
├── ai.py                     # Gemini API, 4 tutoring styles, RAG and quizzes
├── tutoring.py               # Teaching levels, quiz score rules, missed-question recovery
├── requirements.txt
├── requirements-video.txt    # Optional faster-whisper
├── .env.example
├── .gitignore
├── .streamlit/config.toml
├── sample_materials/photosynthesis.txt
├── tests/test_core.py
└── tests/test_tutoring.py
```

On first run, the app creates `data/studymate.sqlite3` locally. This folder is ignored by Git. If you delete it, your indexed sources and attempts are lost. The active tutoring session, previous tutoring sessions, and current quiz are **session-only** and reset when a Streamlit session restarts.

## How adaptive quizzes work

- **Mastery** is the weighted percentage correct across up to 12 recent attempts *per topic*, with higher weight for hard questions.
- Students choose **easy**, **medium**, or **hard** before generating each quiz. Mastery suggests a starting level: easy below 40%, medium from 40–74%, and hard at 75%+; students can override it.
- A new topic has an initial **45% baseline** used for the suggested difficulty, not a measured skill score.
- Each quiz attempt records the selected difficulty, and weaker topics appear as revision recommendations.
- A **single quiz score below 60%** offers *optional* tutoring for a **specific missed question** (not just the broad topic). The student may decline. At 60–79%, the app suggests revision; at 80%+, it encourages another quiz.
- Tutorial difficulty is separate from quiz difficulty: the student decides when to request a simpler teaching style.

## Important limitations / safe practices

- **Source grounding:** citations link the generated response to retrieved passages, but an LLM can still make mistakes. Verify critical explanations manually. The app includes the original passages for inspection.
- **Text extraction:** scanned PDFs and figures without selectable text are not OCR'd. PPTX charts or images are not interpreted. Whisper handles speech audio only, not video frames.
- **Retrieval:** TF-IDF is lightweight and keyword-based; semantic embeddings/ChromaDB are an optional upgrade.
- **Data privacy:** diagram images are sent to Google's Gemini API when analyzed. Asking questions with Gemini also sends selected source passages. Only upload materials you're allowed to share, and review generated descriptions for mistakes.
- **Security:** web imports are limited to public HTTP(S) pages and standard ports. Do not upload sensitive information into this prototype, expose the app to the public internet, or commit `.env`.
- **LLM questions:** auto-generated multiple choice questions can be flawed; verify correct answers against the source passages during your demo.

## Next improvements if time allows

1. Add an image extraction or vision step for figures in lecture slides.
2. Replace TF-IDF with embedding retrieval (ChromaDB or another vector store).
3. Add timestamp jump links for video segments and a spaced-repetition schedule.
4. Add student accounts and separate progress by user.

## Testing

```bash
python -m unittest discover -s tests -v
```

## Upgrade from the previous StudyMate starter

If your **original project already runs in VS Code**, you **do not need to reinstall everything**.

1. **Stop Streamlit** in VS Code with `Ctrl+C`.
2. Back up your existing StudyMate folder.
3. From this updated ZIP, **replace only** `app.py` and `ai.py` in your existing folder and **add the new** `tutoring.py` alongside them. Leave your existing `.env` and `data/studymate.sqlite3` untouched. You can also copy the new `tests/test_tutoring.py`.
4. Run `python -m streamlit run app.py` again. The existing learning materials and quiz history remain in your original SQLite database.

Alternatively, unzip this as a **new project folder** and copy your old `.env` and `data/studymate.sqlite3` to it yourself if you want to keep your API key and progress. Never share `.env` publicly.

No database schema migration is needed for this update. The four-stage chat history is stored in Streamlit session state, not the SQLite database. Current implementation is designed for **one local student / hackathon demo**. It is not multi-user and does not itself verify whether the student genuinely understands; the student indicates this by clicking a button.
