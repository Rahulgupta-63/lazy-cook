import os
import streamlit as st
from groq import Groq
from dotenv import load_dotenv
from cook_logic import (parse_items, is_safe, generate_plan, TIME_OPTIONS, DIETS, EQUIPMENT)

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

MODEL = "openai/gpt-oss-20b"

st.set_page_config(page_title="Lazy Cook", page_icon="🦥")
st.title("🦥 Lazy Cook")
st.write("Too tired to think? Type what you have. Get one easy Indian dish, "
         "a tiny shopping list (3 items at most), and a few steps that fit your time.")

items_raw = st.text_area("What do you have? (separate with commas)",
                         placeholder="rice, onion, tomato, curd")
time_limit = st.selectbox("Minutes you can spare", TIME_OPTIONS, index=1)
servings = st.slider("Servings", 1, 4, 1)
diet = st.selectbox("Diet", DIETS)
equipment = st.selectbox("What can you cook with?", EQUIPMENT)
avoid = st.text_input("Foods to avoid (optional, separate with commas)")

if st.button("Plan my lazy meal"):
    st.session_state.pop("plan", None)
    st.session_state.pop("problems", None)
    items = parse_items(items_raw)
    if not api_key:
        st.error("API key not found. Check your .env file or Streamlit secrets.")
    elif not items:
        st.warning("Type at least one food item you have.")
    elif not is_safe(items):
        st.warning("One of those items is not food. Please list only food.")
    else:
        data = {"items": items_raw, "time": time_limit, "servings": servings,
                "diet": diet, "equipment": equipment, "avoid": avoid}
        try:
            client = Groq(api_key=api_key, timeout=90)
            with st.spinner("Thinking of something easy..."):
                plan, problems = generate_plan(client, MODEL, data)
            st.session_state["plan"] = plan
            st.session_state["problems"] = problems
        except Exception as e:
            st.error(f"Something went wrong: {e}")

if st.session_state.get("plan"):
    if st.session_state.get("problems"):
        st.warning("The auto-check still flagged: " + "; ".join(st.session_state["problems"]) +
                   ". Please read the recipe carefully before cooking.")
    else:
        st.success("Auto-check passed (time, diet, equipment, shopping list, steps).")
    st.markdown(st.session_state["plan"])
    st.download_button("Download recipe (.txt)", st.session_state["plan"], file_name="lazy-cook.txt")
    st.caption("AI-generated. Check that food is fresh and fully cooked.")
