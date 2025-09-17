"""
Smart Interview Bot - GUI (slide-by-slide)
- Single-file Python app using tkinter (standard library)
- Colorful, professional slides with Next / Previous navigation
- Text-mode answers, keyword-based scoring, per-question feedback

How to run:
1. Save this file as `smart_interview_gui.py`.
2. Run: `python smart_interview_gui.py` (requires Python 3.8+).

Optional enhancements you can add later:
- Speech input with `speech_recognition` and `pyaudio`
- Better NLP scoring with `nltk` or an LLM API
- Export results to PDF using `reportlab`

"""

import tkinter as tk
from tkinter import ttk, messagebox
import random

# --------------------------
# Question bank
# --------------------------
TECHNICAL_QUESTIONS = [
    {"q": "What is the difference between list and tuple in Python?", "keywords": ["mutable", "immutable"]},
    {"q": "Explain the concept of inheritance in OOP.", "keywords": ["inheritance", "base class", "derived", "subclass"]},
    {"q": "What is the time complexity of binary search?", "keywords": ["log", "logarithmic", "O(log n)"]},
]

HR_QUESTIONS = [
    {"q": "Tell me about yourself.", "keywords": ["student", "experience", "project", "goal"]},
    {"q": "What are your strengths and weaknesses?", "keywords": ["strength", "weakness", "learning"]},
    {"q": "Where do you see yourself in 5 years?", "keywords": ["future", "goal", "career"]},
]

# Choose how many from each section
NUM_TECH = 3
NUM_HR = 2

# --------------------------
# Helpers
# --------------------------

def evaluate_answer(answer, keywords):
    """Return matched_count and feedback string"""
    ans = answer.lower()
    matched = 0
    matched_words = []
    for kw in keywords:
        if kw.lower() in ans:
            matched += 1
            matched_words.append(kw)

    if matched == 0:
        fb = "Needs improvement — missing important points."
    elif matched < len(keywords):
        fb = "Good — some important points present, add more details."
    else:
        fb = "Excellent — covered expected points!"

    return matched, fb, matched_words

# --------------------------
# Main App
# --------------------------

class Slide(tk.Frame):
    def __init__(self, master, title="", subtitle="", bg="#ffffff"):
        super().__init__(master, bg=bg)
        self.title = title
        self.subtitle = subtitle
        self.bg = bg
        self._build()

    def _build(self):
        # Title
        self.lbl_title = tk.Label(self, text=self.title, font=("Segoe UI", 20, "bold"), bg=self.bg)
        self.lbl_title.pack(pady=(20, 6))
        # Subtitle
        self.lbl_sub = tk.Label(self, text=self.subtitle, font=("Segoe UI", 11), bg=self.bg, wraplength=760, justify="center")
        self.lbl_sub.pack(pady=(0, 10))


class QuestionSlide(Slide):
    def __init__(self, master, question_data, index, total, bg):
        super().__init__(master, title=f"Question {index}/{total}", subtitle=question_data['q'], bg=bg)
        self.question_data = question_data
        self.index = index
        self.total = total
        self._build_question_area()

    def _build_question_area(self):
        # Text entry for answer
        self.txt = tk.Text(self, height=8, width=90, font=("Segoe UI", 10))
        self.txt.pack(pady=(10, 6))

        # Feedback label
        self.fb_var = tk.StringVar(value="")
        self.lbl_fb = tk.Label(self, textvariable=self.fb_var, font=("Segoe UI", 10, "italic"), bg=self.bg)
        self.lbl_fb.pack(pady=(6, 6))

        # Small hint area to show matched keywords (hidden initially)
        self.hint_var = tk.StringVar(value="")
        self.lbl_hint = tk.Label(self, textvariable=self.hint_var, font=("Segoe UI", 9), bg=self.bg)
        self.lbl_hint.pack(pady=(2, 10))

    def get_answer(self):
        return self.txt.get("1.0", tk.END).strip()

    def set_feedback(self, text):
        self.fb_var.set(text)

    def set_hint(self, text):
        self.hint_var.set(text)


class SummarySlide(Slide):
    def __init__(self, master, summary_text, bg="#f7f7f7"):
        super().__init__(master, title="Interview Summary", subtitle=summary_text, bg=bg)
        self._build_summary()

    def _build_summary(self):
        self.lbl_more = tk.Label(self, text="(Use the buttons below to finish or restart)", bg=self.bg, font=("Segoe UI", 9))
        self.lbl_more.pack(pady=(10, 6))


class SmartInterviewApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Interview Bot")
        self.geometry("820x560")
        self.resizable(False, False)

        # Style
        self.style = ttk.Style(self)
        try:
            self.style.theme_use('clam')
        except Exception:
            pass

        # Color palette
        self.colors = ["#0b6e4f", "#f08a24", "#0d6efd", "#6f42c1", "#198754"]

        # Header area
        self.header = tk.Frame(self, bg=self.colors[2], height=70)
        self.header.pack(fill=tk.X)
        self._build_header()

        # Container for slides
        self.container = tk.Frame(self, bg="#ffffff")
        self.container.pack(fill=tk.BOTH, expand=True)

        # Footer navigation
        self.footer = tk.Frame(self, bg="#f0f0f0", height=70)
        self.footer.pack(fill=tk.X)
        self._build_footer()

        # Prepare interview
        self._prepare_questions()
        self.current_idx = 0
        self.slides = []
        self.answers = [""] * len(self.questions)
        self.scores = [0] * len(self.questions)

        self._build_slides()
        self._show_slide(0)

    def _build_header(self):
        logo = tk.Label(self.header, text="Smart Interview Bot", font=("Segoe UI", 16, "bold"), bg=self.colors[2], fg="white")
        logo.pack(side=tk.LEFT, padx=20)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(self.header, orient='horizontal', length=300, mode='determinate', variable=self.progress_var)
        self.progress.pack(side=tk.RIGHT, padx=20)

    def _build_footer(self):
        self.btn_prev = ttk.Button(self.footer, text="◀ Previous", command=self.prev_slide)
        self.btn_prev.pack(side=tk.LEFT, padx=18, pady=12)

        self.btn_next = ttk.Button(self.footer, text="Next ▶", command=self.next_slide)
        self.btn_next.pack(side=tk.RIGHT, padx=18, pady=12)

        self.btn_submit = ttk.Button(self.footer, text="Submit Answer & Eval", command=self.evaluate_current)
        self.btn_submit.pack(side=tk.RIGHT, padx=12, pady=12)

    def _prepare_questions(self):
        tech_sample = random.sample(TECHNICAL_QUESTIONS, min(NUM_TECH, len(TECHNICAL_QUESTIONS)))
        hr_sample = random.sample(HR_QUESTIONS, min(NUM_HR, len(HR_QUESTIONS)))
        # Interleave tech and hr questions for variety
        combined = []
        for i in range(max(len(tech_sample), len(hr_sample))):
            if i < len(tech_sample):
                combined.append(("Technical", tech_sample[i]))
            if i < len(hr_sample):
                combined.append(("HR", hr_sample[i]))

        self.questions = combined

    def _build_slides(self):
        total = len(self.questions)
        for idx, (sect, qdata) in enumerate(self.questions, start=1):
            color = self.colors[idx % len(self.colors)]
            slide = QuestionSlide(self.container, question_data=qdata, index=idx, total=total, bg=color)
            slide.place(relwidth=1, relheight=1)
            self.slides.append(slide)

        # Summary slide appended at the end
        self.summary_slide = SummarySlide(self.container, summary_text="Your detailed summary will appear here.")
        self.summary_slide.place(relwidth=1, relheight=1)

    def _show_slide(self, idx):
        # idx is 0-based. last index is summary
        for s in self.slides:
            s.lower()
        self.summary_slide.lower()

        if idx < len(self.slides):
            self.slides[idx].lift()
        else:
            self.summary_slide.lift()

        # Update progress
        percent = (idx / (len(self.slides))) * 100
        self.progress_var.set(percent)

        # Update nav buttons
        self.btn_prev['state'] = tk.NORMAL if idx > 0 else tk.DISABLED
        self.btn_next['state'] = tk.NORMAL if idx < len(self.slides) else tk.DISABLED

        self.current_idx = idx

    def evaluate_current(self):
        if self.current_idx >= len(self.slides):
            return

        slide = self.slides[self.current_idx]
        ans = slide.get_answer()
        self.answers[self.current_idx] = ans
        matched, feedback, matched_words = evaluate_answer(ans, slide.question_data['keywords'])
        self.scores[self.current_idx] = matched
        slide.set_feedback(feedback)
        if matched_words:
            slide.set_hint("Matched keywords: " + ", ".join(matched_words))
        else:
            slide.set_hint("")

        messagebox.showinfo("Evaluation", f"Feedback:\n{feedback}")

    def next_slide(self):
        # Auto-evaluate before moving on
        self.evaluate_current()
        if self.current_idx < len(self.slides) - 1:
            self._show_slide(self.current_idx + 1)
        else:
            # Move to summary
            self._show_summary()

    def prev_slide(self):
        if self.current_idx > 0:
            self._show_slide(self.current_idx - 1)

    def _show_summary(self):
        # Build a summary string
        total_keywords = sum(len(q[1]['keywords']) for q in self.questions)
        total_score = sum(self.scores)
        section_wise = {}
        for i, (sect, qdata) in enumerate(self.questions):
            section_wise.setdefault(sect, {'score': 0, 'possible': 0})
            section_wise[sect]['score'] += self.scores[i]
            section_wise[sect]['possible'] += len(qdata['keywords'])

        lines = [f"Total Score: {total_score} / {total_keywords}", ""]
        for sect, vals in section_wise.items():
            lines.append(f"{sect} Score: {vals['score']} / {vals['possible']}")
        lines.append("")
        lines.append("Detailed answers and feedback:")

        for i, (sect, qdata) in enumerate(self.questions):
            ans = self.answers[i].strip() or "(No answer)"
            matched = self.scores[i]
            possible = len(qdata['keywords'])
            lines.append(f"Q{i+1} ({sect}): {qdata['q']}")
            lines.append(f"  Your answer: {ans}")
            lines.append(f"  Score: {matched} / {possible}")
            lines.append("")

        summary_text = "\n".join(lines)
        # Put text into summary slide subtitle area
        self.summary_slide.lbl_sub.config(text=summary_text)
        self._show_slide(len(self.slides))


# --------------------------
# Run
# --------------------------
if __name__ == '__main__':
    app = SmartInterviewApp()
    app.mainloop()
