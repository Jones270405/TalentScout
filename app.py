import streamlit as st
import json, os, time
from cryptography.fernet import Fernet
import ollama

# ================== CONFIG ==================
MODEL_NAME = "tinyllama"   # LOW-RAM OFFLINE MODEL
DATA_FILE = "candidates.enc"
KEY_FILE = "secret.key"

# ================== SECURITY (GDPR) ==================
if not os.path.exists(KEY_FILE):
    with open(KEY_FILE, "wb") as f:
        f.write(Fernet.generate_key())

with open(KEY_FILE, "rb") as f:
    fernet = Fernet(f.read())

def save_candidate(data):
    encrypted = fernet.encrypt(json.dumps(data).encode())
    with open(DATA_FILE, "ab") as f:
        f.write(encrypted + b"\n")

def load_candidates():
    if not os.path.exists(DATA_FILE):
        return []
    records = []
    with open(DATA_FILE, "rb") as f:
        for line in f:
            try:
                records.append(json.loads(fernet.decrypt(line.strip())))
            except:
                pass
    return records

# ================== UTILITIES ==================
def detect_sentiment(text):
    t = text.lower()
    if any(w in t for w in ["sad", "bad", "not good", "tired", "stress"]):
        return "Negative"
    if any(w in t for w in ["good", "great", "happy"]):
        return "Positive"
    return "Neutral"

def sentiment_prefix(sentiment):
    if sentiment == "Negative":
        return "I’m sorry you’re feeling this way. Take your time. "
    if sentiment == "Positive":
        return "That’s great to hear!"
    return ""

def generate_questions(tech):
    prompt = f"""
Generate interview questions for {tech}.
Only output questions.
"""

    try:
        response = ollama.generate(
            model=MODEL_NAME,
            prompt=prompt,
            options={"temperature": 0}
        )

        questions = []
        for line in response["response"].split("\n"):
            line = line.strip()
            if (
                line.endswith("?")
                and "answer" not in line.lower()
                and "corresponding" not in line.lower()
                and len(line) > 15
            ):
                questions.append(line)

        return questions[:3]

    except Exception:
        #FALLBACK QUESTIONS (if Ollama not available)
        return [
            f"What are the core concepts of {tech}?",
            f"Explain a real-world use case of {tech}.",
            f"What challenges have you faced while working with {tech}?"
        ]


def generate_reference_answer(question, tech):
    prompt = f"""
You are an interview expert.
Give a clear, correct, concise reference answer
for the following interview question.

Technology: {tech}
Question: {question}

Do NOT mention the question again.
"""

    try:
        response = ollama.generate(
            model=MODEL_NAME,
            prompt=prompt,
            options={"temperature": 0}
        )
        return response["response"].strip()

    except Exception:
        # FALLBACK REFERENCE ANSWER
        return (
            f"A good answer should explain the fundamental concepts of {tech}, "
            f"describe how it is used in real-world applications, and highlight "
            f"best practices, advantages, and limitations clearly."
        )

def evaluate_answer(answer):
    if len(answer.strip()) < 15:
        return False, "That answer seems a bit short. Could you explain a bit more?"
    return True, "Thanks for your response."

# ================== SESSION INIT ==================
if "step" not in st.session_state:
    st.session_state.step = 0
    st.session_state.messages = []
    st.session_state.candidate = {}
    st.session_state.questions = []
    st.session_state.q_index = 0
    st.session_state.tech_confirmed = False

# ================== SIDEBAR ==================
st.sidebar.title("TalentScout")

if st.sidebar.button("New Candidate / Reset"):
    st.session_state.clear()
    st.rerun()

st.sidebar.markdown("### Candidates")
for c in load_candidates():
    st.sidebar.markdown(f"""
Name:**{c.get('name')}**  
Email:{c.get('email')}  
Phone: {c.get('phone')}  
Position: {c.get('position')}  
Tech Stack: {c.get('tech_stack')}  
Location: {c.get('location')}
---
""")

# ================== CHAT UI ==================
st.title("TalentScout Hiring Assistant")
st.info("If not feeling well, you can just write keywords: sad, bad, not good, tired, stress")
st.info("If feeling well, start with keywords like: good,great and happy")

for m in st.session_state.messages:
    st.chat_message(m["role"]).write(m["content"])

user_input = st.chat_input("Type your message...")

# ================== WAIT FOR GREETING ==================
if st.session_state.step == 0 and not user_input:
    st.chat_message("assistant").write(
        "Hi! Please say hello to begin the TalentScout screening."
    )
    st.stop()

# ================== PROCESS USER INPUT ==================
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    sentiment = detect_sentiment(user_input)
    prefix = sentiment_prefix(sentiment)

    # -------- FLOW --------
    if st.session_state.step == 0:
        reply = "Welcome to TalentScout! What is your **full name**?"
        st.session_state.step = 1

    elif st.session_state.step == 1:
        st.session_state.candidate["name"] = user_input
        reply = f"Hi **{user_input}**! What is your **email address**?"
        st.session_state.step = 2

    elif st.session_state.step == 2:
        if "@" not in user_input:
            reply = prefix + "Please enter a valid email address."
        else:
            st.session_state.candidate["email"] = user_input
            reply = "Please share your **phone number** (digits only)."
            st.session_state.step = 3

    elif st.session_state.step == 3:
        if not user_input.isdigit() or not (7 <= len(user_input) <= 15):
            reply = prefix + "That doesn’t look valid. Please try again."
        else:
            st.session_state.candidate["phone"] = user_input
            reply = "How many **years of professional experience** do you have?"
            st.session_state.step = 4

    elif st.session_state.step == 4:
        years = int(user_input)
        st.session_state.candidate["experience"] = years
        if years < 2:
            reply = (
                "Thanks for sharing, To strengthen your profile:\n"
                "- Build strong projects\n"
                "- Practice fundamentals\n"
                "- Contribute to GitHub\n\n"
                "Please select your **position** below."
            )
        else:
            reply = "Great! Please select your **position** below."
        st.session_state.step = 5

    elif st.session_state.step == 9:
        choice = user_input.lower()
        if "new" in choice or "start" in choice:
            st.session_state.clear()
            st.rerun()
        elif "exit" in choice or "no" in choice:
            reply = "Thank you for using TalentScout!"
            st.session_state.step = 0
        else:
            reply = "Please type **start new** or **exit**."

    else:
        reply = None

    if reply:
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.chat_message("assistant").write(reply)

# ================== DROPDOWNS ==================
if st.session_state.step == 5:
    position = st.selectbox(
        "Select your position",
        ["Backend Developer", "Frontend Developer", "Data Scientist", "AI/ML Engineer"]
    )
    if st.button("Confirm Position"):
        st.session_state.candidate["position"] = position
        st.session_state.messages.append(
            {"role": "user", "content": f"I am applying for {position}"}
        )
        st.session_state.messages.append(
            {"role": "assistant", "content": "Thanks! Please select your preferred region."}
        )
        st.session_state.step = 6
        st.rerun()

elif st.session_state.step == 6:
    region = st.selectbox("Select your region", ["India", "Europe", "USA", "Remote"])
    if st.button("Confirm Region"):
        st.session_state.candidate["location"] = region
        st.session_state.messages.append(
            {"role": "user", "content": f"My preferred region is {region}"}
        )
        st.session_state.messages.append(
            {"role": "assistant", "content": "Great! Now select your primary tech stack."}
        )
        st.session_state.step = 7
        st.rerun()

elif st.session_state.step == 7 and not st.session_state.tech_confirmed:
    tech_main = st.selectbox(
        "Primary tech stack",
        ["Python", "Java", "JavaScript", "Machine Learning"]
    )

    extra_skills = st.text_input(
        "Other skills (optional, comma separated)",
        placeholder="e.g. Django, SQL, Docker"
    )

    if st.button("Confirm Tech Stack"):
        st.session_state.tech_confirmed = True

        full_stack = tech_main
        if extra_skills.strip():
            full_stack += ", " + ", ".join(
                s.strip() for s in extra_skills.split(",") if s.strip()
            )

        st.session_state.candidate["tech_stack"] = full_stack

        st.session_state.messages.append(
            {"role": "user", "content": f"My tech stack is {full_stack}"}
        )
        st.session_state.messages.append(
            {"role": "assistant", "content": "Generating technical questions… ⏳"}
        )

        with st.spinner("Generating technical questions…"):
            st.session_state.questions = generate_questions(full_stack)
            st.session_state.q_index = 0

        if not st.session_state.questions:
            save_candidate(st.session_state.candidate)
            st.session_state.messages.append(
                {"role": "assistant", "content": "Unable to generate questions. Interview completed."}
            )
            st.session_state.step = 9
        else:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"Technical Question 1:\n\n{st.session_state.questions[0]}"
                }
            )
            st.session_state.step = 8

        st.rerun()

elif st.session_state.step == 8 and user_input:
    ok, feedback = evaluate_answer(user_input)
    st.session_state.messages.append({"role": "assistant", "content": feedback})

    # Generate reference answer (learning purpose)
    ref_answer = generate_reference_answer(
        st.session_state.questions[st.session_state.q_index],
        st.session_state.candidate["tech_stack"]
    )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": f"**Reference Answer (for learning):**\n\n{ref_answer}"
        }
    )

    if not ok:
        st.rerun()

    st.session_state.q_index += 1

    if st.session_state.q_index < len(st.session_state.questions):
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"Technical Question {st.session_state.q_index + 1}:\n\n"
                           f"{st.session_state.questions[st.session_state.q_index]}"
            }
        )
    else:
        save_candidate(st.session_state.candidate)
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "Interview complete.\n\n"
                    "Would you like to **start new** or **exit**?"
                )
            }
        )
        st.session_state.step = 9

    st.rerun()
