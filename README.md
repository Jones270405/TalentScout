# TalentScout – AI-Powered Hiring Assistant 

TalentScout is an AI-driven hiring assistant built using Streamlit and Large Language Models.  
It automates candidate screening through conversational interaction, sentiment detection, and technical questioning.

---

## Features

- Conversational candidate screening
- Sentiment-aware responses
- Role, location & tech stack selection
- AI-generated technical interview questions
- Reference answers for learning
- Secure encrypted candidate data storage (GDPR-friendly)
- Offline LLM support using Ollama

---

## Tech Stack

- Python
- Streamlit
- Ollama (TinyLLaMA)
- Cryptography (Fernet encryption)
- Git & GitHub

---

## How It Works

1. Candidate interacts via chat
2. Personal & professional details are collected
3. AI generates role-specific interview questions
4. Candidate answers are evaluated
5. Reference answers are shown for learning
6. Candidate data is securely stored

---

## Deployment Note

This project uses **Ollama**, which requires a local runtime.
Cloud platforms do not support Ollama yet.

Therefore:
- App is demonstrated **locally**
- Demo video is provided instead of hosted link

---

## Run Locally

```bash
pip install -r requirements.txt
ollama run tinyllama
streamlit run app.py
