import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
from PIL import Image
import io

# Load environment variables from .env file
load_dotenv()

CORRECT_PASSCODE = os.getenv("APP_PASSCODE")
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("## 🔐 Authentication")
    with st.form("passcode_form"):
        passcode_input = st.text_input("Passcode", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if passcode_input == CORRECT_PASSCODE:
                st.session_state.authenticated = True
                st.success("✅ Access granted!")
                st.rerun()  # Reload to show app
            else:
                st.error("❌ Incorrect passcode. Try again.")
    st.stop()

# Configure Google Gemini API
try:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    st.error(f"Error configuring Gemini API. : {e}")
    st.stop() # Stop the app if API key is not configured
    
# Function to generate image  using Gemini API
def generate_image_with_gemini(prompt_text, include_text):
    """Generates an image using the Gemini API based on the provided text."""
    try:
        if include_text:
            full_prompt = (
                f"GENERATE A PROFESSIONAL VISUAL IMAGE in a vibrant, highly detailed, animated illustration style. "
                f"The image MUST have a precise **16:9 widescreen aspect ratio**. "
                f"Ensure that **the provided Hindi text or words are clearly visible and well-integrated** into the image design — like on banners, signs, papers, or visually appropriate elements. "
                f"The Hindi text must appear **readable, naturally embedded**, and **not distorted**. "
                f"Every element described in the following Hindi input must be included:\n\n"
                f"'{prompt_text}'"
            )
        else:
            if len(prompt_text.split()) <= 8:
                context_description = f"एक दृश्य जिसमें {prompt_text} पूरी तरह से प्राकृतिक रूप से चित्रित हो। यह सिर्फ एक लेबल नहीं है, बल्कि एक पूर्ण वातावरण और दृश्य होना चाहिए। किसी भी प्रकार का पाठ या शब्द चित्र में नहीं होना चाहिए।"
            else:
                context_description = prompt_text
            
            full_prompt = (
                f"STRICTLY GENERATE A VISUAL IMAGE. "
                f"The image MUST be a vibrant, highly detailed, professional **animated illustration**. "
                f"It MUST have a **16:9 widescreen aspect ratio**. "
                f"**DO NOT INCLUDE ANY TEXT OR WRITING** in the image — this includes but is not limited to signs, labels, posters, screens, papers, books, symbols, characters, or written language in any form. "
                f"The image MUST NOT contain any alphabetic or numeric characters. "
                f"**NO TEXT OR SYMBOLS** should appear anywhere in the final image. "
                f"CRITICALLY IMPORTANT: Every visual element, character, object, and environmental detail described in the following Hindi text MUST be visually represented with high fidelity. "
                f"DO NOT OMIT ANY DETAIL. "
                f"Generate a vivid and complete scene that perfectly visualizes the following Hindi description:\n\n"
                f"'{context_description}'"
            )

        st.info("Attempting to generate image... This may take a moment.")
        
        # Call generate_content with responseModalities to request image output
        response = client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=full_prompt,
            config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE']
            )
        )
        
        generated_image_found = False
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                st.write("**Gemini's Text Response (if any):**")
                st.write(part.text)
            elif part.inline_data is not None:
                st.success("✅ Image successfully generated!")
                img = Image.open(io.BytesIO((part.inline_data.data)))
                st.image(img, caption="Generated Image", use_container_width=True)
                
                # Resize to 1920x1080
                resized_img = img.resize((1920, 1080), Image.LANCZOS)
                
                img_byte_arr = io.BytesIO()
                resized_img.save(img_byte_arr, format="PNG")
                img_bytes = img_byte_arr.getvalue()
                # Download button
                st.download_button(
                    label="⬇️ Download Image",
                    data=img_bytes,
                    file_name="animation.png", # You can make this dynamic
                    mime=part.inline_data.mime_type
                )
                generated_image_found = True
                break
        
        if not generated_image_found:
            st.warning("⚠️ Gemini API did not return an image directly for this prompt. It might have returned only text or encountered an internal issue.")
            if response.text:
                st.write("Full response text for debugging:")
                st.write(response.text)
            st.error("🛑 Please try a different prompt or check the Gemini API documentation for supported image generation formats and limitations.")

    except Exception as e:
        st.error(f"🛑 Error generating image: {e}")

# Streamlit UI
st.set_page_config(page_title="Image Generator", page_icon="✨")

st.markdown("<h3 style='text-align: center;'>🎨 Image Generator 🎨</h3>", unsafe_allow_html=True)
st.markdown("""
### 📝 Description
Enter a Hindi prompt below and generate a **high-resolution animated-style image**.

🌟 The image will be:
- Professional
- Highly detailed
- With a 16:9 aspect ratio
""")

hindi_text_input = st.text_area(
    "💬 Enter Hindi text for your image:",
    placeholder="उदाहरण: एक जंगल में नाचती हुई एक छोटी परी, चमकती हुई पंखों के साथ।",
    height=300
)
include_text = st.checkbox("Image with Text")

if st.button("✨ Generate Image"):
    if hindi_text_input:
        with st.spinner("🎨 Creating a beautiful image for you..."):
            generate_image_with_gemini(hindi_text_input, include_text)
            # generate_genai(hindi_text_input)
    else:
        st.warning("⚠️ Please enter some Hindi text for your image.")