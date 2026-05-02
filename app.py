import streamlit as st
from groq import Groq

# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────

# Put your API key here
client = Groq(api_key="Put your API key here")

st.set_page_config(page_title="Study Coach AI", page_icon="🎓", layout="centered")

# ─────────────────────────────────────────────
# SESSION STATE (acts as memory during the session)
# ─────────────────────────────────────────────

# These variables are remembered as long as the app is open
if "messages" not in st.session_state:
    st.session_state.messages = []   # chat history

if "notes" not in st.session_state:
    st.session_state.notes = ""      # the student's uploaded notes

if "score" not in st.session_state:
    st.session_state.score = {"correct": 0, "total": 0}   # quiz score tracker

if "weak_topics" not in st.session_state:
    st.session_state.weak_topics = []   # topics the student got wrong

# ─────────────────────────────────────────────
# SYSTEM PROMPT (tells the AI how to behave)
# ─────────────────────────────────────────────

def build_system_prompt():
    weak = ", ".join(st.session_state.weak_topics) if st.session_state.weak_topics else "none identified yet"
    notes_section = f"\n\nHere are the student's notes:\n{st.session_state.notes}" if st.session_state.notes else ""

    return f"""You are a helpful and encouraging study coach AI.

Your job is to:
1. Quiz the student based on their uploaded notes
2. Give short, clear explanations when they get something wrong
3. Focus more on weak topics when quizzing

Current weak topics: {weak}
Quiz score so far: {st.session_state.score['correct']} correct out of {st.session_state.score['total']} questions

When the student asks to be quizzed:
- Ask ONE question at a time
- Wait for their answer before asking the next
- After they answer, say if they were RIGHT or WRONG
- If wrong, give a short explanation
- Always end with "Type 'quiz me' for another question or ask me anything."

Be friendly, encouraging, and patient.{notes_section}"""


# ─────────────────────────────────────────────
# FUNCTION: Send message to OpenAI
# ─────────────────────────────────────────────

def chat(user_message):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_message})

    # Build the full conversation to send to OpenAI
    full_conversation = [{"role": "system", "content": build_system_prompt()}]
    full_conversation += st.session_state.messages

    # Call the OpenAI API
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=full_conversation
    )

    # Extract the reply text
    reply = response.choices[0].message.content

    # Add AI reply to history
    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Check if the AI said RIGHT or WRONG and update the score
    if "RIGHT" in reply.upper() or "CORRECT" in reply.upper():
        st.session_state.score["correct"] += 1
        st.session_state.score["total"] += 1
    elif "WRONG" in reply.upper() or "INCORRECT" in reply.upper():
        st.session_state.score["total"] += 1
        # Try to detect what topic was wrong from user's message
        if len(user_message) > 3:
            st.session_state.weak_topics.append(user_message[:40])
            # Keep only the last 5 weak topics
            st.session_state.weak_topics = st.session_state.weak_topics[-5:]

    return reply


# ─────────────────────────────────────────────
# UI: PAGE HEADER
# ─────────────────────────────────────────────

st.title("🎓 Study Coach AI")
st.caption("Upload your notes, get quizzed, and track your weak spots.")

# ─────────────────────────────────────────────
# UI: SIDEBAR (notes input + score display)
# ─────────────────────────────────────────────

with st.sidebar:
    st.header("📚 Your Notes")
    st.caption("Paste your study notes below. The AI will quiz you on them.")

    notes_input = st.text_area(
        "Paste notes here",
        height=250,
        placeholder="e.g. Photosynthesis is the process by which plants use sunlight..."
    )

    if st.button("Load Notes ✅"):
        st.session_state.notes = notes_input
        st.success("Notes loaded! Now go ask to be quizzed.")

    st.divider()

    # Score display
    st.header("📊 Your Score")
    score = st.session_state.score
    if score["total"] > 0:
        pct = int((score["correct"] / score["total"]) * 100)
        st.metric("Score", f"{score['correct']} / {score['total']}", f"{pct}%")
    else:
        st.info("No questions answered yet.")

    # Weak topics display
    if st.session_state.weak_topics:
        st.header("⚠️ Weak Topics")
        for t in st.session_state.weak_topics[-5:]:
            st.write(f"• {t}")

    st.divider()

    # Reset button
    if st.button("🔄 Reset Session"):
        for key in ["messages", "notes", "score", "weak_topics"]:
            del st.session_state[key]
        st.rerun()


# ─────────────────────────────────────────────
# UI: CHAT AREA
# ─────────────────────────────────────────────

# Show all previous messages
for msg in st.session_state.messages:
    role = "You" if msg["role"] == "user" else "Coach"
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Welcome message if chat is empty
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.write("👋 Hi! I'm your Study Coach. Paste your notes in the sidebar, then type **'quiz me'** to get started!")

# ─────────────────────────────────────────────
# UI: CHAT INPUT
# ─────────────────────────────────────────────

user_input = st.chat_input("Ask a question or type 'quiz me'...")

if user_input:
    # Show user message
    with st.chat_message("user"):
        st.write(user_input)

    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = chat(user_input)
        st.write(reply)
