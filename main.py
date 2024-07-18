import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import base64
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the API key
api_key = os.getenv("API_KEY")

# Configure your library with the API key
genai.configure(api_key=api_key)

# Configure Gemini API
genai.configure(api_key="AIzaSyAC4I_DbfMD0iK96J-4gjO87y4jW4gHZ7s")

# Gemini model
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# Streamlit app
st.set_page_config(layout="wide")
st.title("Exercise Chatbot")

# Initialize chat history and image history
if "messages" not in st.session_state:
    st.session_state.messages = []
if "image_history" not in st.session_state:
    st.session_state.image_history = []

# Function to convert image to base64
def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Function to convert base64 to image
def base64_to_image(base64_string):
    return Image.open(io.BytesIO(base64.b64decode(base64_string)))

# Sidebar for user inputs
with st.sidebar:
    st.header("Your Profile")
    height = st.number_input("Height (cm)", min_value=100, max_value=250, value=170)
    weight = st.number_input("Weight (kg)", min_value=30, max_value=300, value=70)
    gender = st.radio("Gender", ["Male", "Female", "Other"])
    diet_preference = st.selectbox("Diet Preference", ["No Preference", "Vegetarian", "Vegan", "Keto", "Paleo", "Mediterranean"])
    exercise_frequency = st.select_slider("Exercise Frequency (days per week)", options=[0, 1, 2, 3, 4, 5, 6, 7], value=3)
    goal = st.selectbox("Fitness Goal", ["Weight Loss", "Muscle Gain", "Maintain Weight", "Improve Overall Fitness"])

# Main chat area
chat_container = st.container()

# Input area
input_container = st.container()

with input_container:
    col1, col2 = st.columns([6, 1])
    with col1:
        text_input = st.text_input("Type your message...", key="text_input")
        uploaded_file = st.file_uploader("Attach image (optional)", type=["jpg", "jpeg", "png"], key="file_uploader")
    with col2:
        send_button = st.button("Send", use_container_width=True)

def get_conversation_history(messages, limit=5):
    history = []
    for msg in messages[-limit*2:]:
        role = "Human" if msg["role"] == "user" else "Assistant"
        history.append(f"{role}: {msg['content']}")
    return "\n".join(history)

def get_user_profile():
    return f"""Height: {height}cm, Weight: {weight}kg,
Gender: {gender},
Diet Preference: {diet_preference},
Exercise Frequency: {exercise_frequency} days per week,
Fitness Goal: {goal}"""

if send_button or (text_input and text_input != st.session_state.get("last_text_input", "")):
    st.session_state["last_text_input"] = text_input
    
    conversation_history = get_conversation_history(st.session_state.messages)
    user_profile = get_user_profile()
    
    prompt = f"""Recent conversation:
{conversation_history}

User Profile:
{user_profile}

New message: {text_input or "Analyze all stats of workout like caloreis,distance if applicable,steps if applicable,time,etc."}

STRICTLY ANSWER QUERIES RELATED TO FITNESS,WORKOUT,NUTRITION,DIET ONLY. REFUSE TO ANSWER ANYTHING ELSE."""

    content = [prompt]
    
    # Include all previous images in the context
    for img in st.session_state.image_history:
        content.append(base64_to_image(img))
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        content.append(image)
        image_base64 = image_to_base64(image)
        st.session_state.image_history.append(image_base64)
    else:
        image_base64 = None

    user_message = f"{user_profile}\n\n{text_input}"
    message_data = {"role": "user", "content": user_message}
    if image_base64:
        message_data["image"] = image_base64
    st.session_state.messages.append(message_data)
    
    response = model.generate_content(content)
    st.session_state.messages.append({"role": "assistant", "content": response.text})

# Display chat messages
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "image" in message:
                st.image(base64_to_image(message["image"]), caption="Uploaded Image", width=200)

# Clear chat history button
if st.sidebar.button("Clear Chat History"):
    st.session_state.messages = []
    st.session_state.image_history = []
    st.experimental_rerun()
