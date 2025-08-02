import streamlit as st
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()  # Load .env file

# Now you can access your key securely:
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

import google.generativeai as genai
genai.configure(api_key=GOOGLE_API_KEY)

PROFILE_DIR = "profiles"
os.makedirs(PROFILE_DIR, exist_ok=True)

# --- FILE I/O HELPERS ---
def save_profile(name, style_summary):
    with open(os.path.join(PROFILE_DIR, f"{name}.json"), "w") as f:
        json.dump({"style": style_summary}, f)

def load_profiles():
    return [f[:-5] for f in os.listdir(PROFILE_DIR) if f.endswith(".json")]

def get_profile(name):
    with open(os.path.join(PROFILE_DIR, f"{name}.json"), "r") as f:
        return json.load(f)["style"]

# --- AI FUNCTIONS ---
def analyze_style(posts):
    prompt = f"""
You are a writing style analyzer. Analyze the following LinkedIn posts and summarize the author's writing style.

Posts:
{"\n\n".join(posts)}

Return:
- Tone
- Sentence style
- Emoji or formatting patterns
- Common structure (e.g., hooks, storytelling, advice, questions)
- Typical vocabulary or phrases
"""
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text.strip()

def generate_post(style_description, user_prompt, tone="Default"):
    prompt = f"""
You are an AI that writes LinkedIn posts in a person's custom writing style.

Writing Style:
{style_description}

Write a new LinkedIn post based on this prompt:
"{user_prompt}"

Tone: {tone if tone != "Default" else "Match original style"}

Keep it natural and consistent with the writing style.
"""
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text.strip()

def suggest_hashtags(post_content):
    prompt = f"Suggest 5 relevant LinkedIn hashtags (without # symbols) for this post:\n\n{post_content}"
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text.strip().replace("\n", "  •  #")

# --- STREAMLIT UI ---
st.set_page_config(page_title="LinkedIn Post Generator", layout="centered")
st.title("💼 LinkedIn Post Generator")
st.subheader("✨ Style-matched posts, powered by Gemini")
st.markdown("Paste 2–10 of your previous LinkedIn posts below, or select a saved style profile. Then enter a new idea and get your next post — written in your voice.")

# --- PROFILE SELECTION ---
st.markdown("### 👤 Writing Style Profiles")
profile_option = st.selectbox("Choose a profile or create new:", ["Create New"] + load_profiles())
style_summary = ""

if profile_option == "Create New":
    profile_name = st.text_input("Enter a name for your new style profile")
else:
    style_summary = get_profile(profile_option)
    st.success(f"Loaded profile: {profile_option}")

st.markdown("---")

# --- COLLECT POSTS IF NEW PROFILE ---
if profile_option == "Create New":
    num = st.slider("How many past posts do you want to provide?", 2, 10, 3)
    previous_posts = []
    for i in range(num):
        post = st.text_area(f"Post #{i + 1}", height=100, key=f"post_{i}")
        if post:
            previous_posts.append(post)
else:
    previous_posts = []

# --- INPUT: New Prompt ---
user_prompt = st.text_input("📝 What should your next post be about?")

# --- INPUT: Tone Selector ---
tone_choice = st.selectbox(
    "🎭 Optional: Adjust the tone of your post",
    ["Default", "Inspirational", "Professional", "Friendly", "Witty"]
)

generate_clicked = st.button("Generate My Post ✍️")

# --- GENERATION FLOW ---
if generate_clicked and user_prompt and (style_summary or len(previous_posts) >= 2):

    # Step 1: Analyze Style (if creating new)
    if not style_summary:
        with st.spinner("Analyzing your writing style..."):
            style_summary = analyze_style(previous_posts)
        st.success("Style analysis complete!")
        st.markdown("### 🧠 Writing Style Summary")
        st.markdown(f"```markdown\n{style_summary}\n```")

        if profile_name:
            save_profile(profile_name, style_summary)
            st.success(f"Profile saved: {profile_name}")

    # Step 2: Generate Post
    with st.spinner("Writing your new post..."):
        final_post = generate_post(style_summary, user_prompt, tone_choice)

    st.markdown("### ✅ Your New LinkedIn Post")
    st.text_area("Final Post", final_post, height=250, key="final_post_box")

    # Step 3: Suggest Hashtags
    with st.spinner("Finding hashtags..."):
        hashtags = suggest_hashtags(final_post)

    st.markdown("### 🔗 Suggested Hashtags")
    st.markdown(f"**#**{hashtags}")

    # Step 4: Copy Button (JS)
    st.markdown("""
        <button onclick="copyToClipboard()" style="margin-top:10px;">📋 Copy to Clipboard</button>
        <script>
        function copyToClipboard() {
            const textarea = document.querySelector('textarea[aria-label="Final Post"]');
            if (textarea) {
                textarea.select();
                document.execCommand('copy');
                alert('Copied to clipboard!');
            }
        }
        </script>
    """, unsafe_allow_html=True)

elif generate_clicked:
    st.warning("Please enter at least 2 valid posts and a prompt, or select a saved profile.")

st.markdown("---")
