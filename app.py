import streamlit as st
from recipe_processor import convert_to_audio_steps

st.set_page_config(page_title="Recipe Audio Assistant", layout="centered")

st.title("🎙️ Recipe Audio Assistant")
st.write("Convert recipes into short, audio-friendly cooking steps.")

recipe_text = st.text_area("Enter recipe text:", height=300)

speech_rate = st.slider(
    "Speech speed",
    min_value=120,
    max_value=220,
    value=165,
    step=5
)

col1, col2 = st.columns(2)

convert_steps = col1.button("Convert to Steps")
convert_audio = col2.button("Convert to Audio")

if convert_steps and recipe_text.strip():
    steps, _ = convert_to_audio_steps(recipe_text)
    st.subheader("Cooking Steps")
    for step in steps:
        st.write(step)

elif convert_audio and recipe_text.strip():
    steps, audio_bytes = convert_to_audio_steps(
        recipe_text,
        with_audio=True,
        speech_rate=speech_rate
    )

    st.subheader("Cooking Steps")
    for step in steps:
        st.write(step)

    if audio_bytes:
        st.subheader("Listen")
        st.audio(audio_bytes, format="audio/mp3")

elif (convert_steps or convert_audio) and not recipe_text.strip():
    st.warning("Please paste a recipe first.")
