import streamlit as st
import requests
import json
import time

# Configure the page
st.set_page_config(
    page_title="LLM Translator",
    page_icon="🌐",
    layout="wide"
)

# Define supported languages
LANGUAGES = {
    "English": "English",
    "Spanish": "Spanish",
    "French": "French",
    "German": "German",
    "Italian": "Italian",
    "Portuguese": "Portuguese",
    "Russian": "Russian",
    "Chinese": "Chinese",
    "Japanese": "Japanese",
    "Korean": "Korean",
    "Arabic": "Arabic",
    "Hindi": "Hindi"
}

# Initialize session state variables if they don't exist
if 'translated_text' not in st.session_state:
    st.session_state.translated_text = ""
if 'source_text' not in st.session_state:
    st.session_state.source_text = ""

def check_backend_health():
    """Check if the backend service is available"""
    try:
        response = requests.get("http://backend:8000/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            if health_data.get("status") == "warning":
                return False, health_data.get("message", "Backend service is available but has warnings")
            return True, "Backend service is available"
        return False, f"Backend service returned status code {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Backend service is not available: {str(e)}"

def translate_text(text, source_lang, target_lang):
    """
    Send a translation request to the backend service
    """
    url = "http://backend:8000/translate"
    data = {
        "text": text,
        "source_language": source_lang,
        "target_language": target_lang
    }
    
    try:
        # Add timeout to prevent hanging requests
        response = requests.post(url, json=data, timeout=30)
        
        # Check for successful response
        if response.status_code == 200:
            response_data = response.json()
            translated_text = response_data.get("translated_text")
            model_used = response_data.get("model_used", "Unknown model")
            return translated_text, model_used, None
        
        # Handle error responses with proper error messages
        error_detail = "Unknown error"
        try:
            error_json = response.json()
            if "detail" in error_json:
                error_detail = error_json["detail"]
        except:
            error_detail = f"HTTP error: {response.status_code}"
        
        return None, None, error_detail
        
    except requests.exceptions.ConnectTimeout:
        return None, None, "Connection timeout: The backend service took too long to respond. Please try again later."
    except requests.exceptions.ReadTimeout:
        return None, None, "Read timeout: The translation request took too long to complete. Please try again with a shorter text."
    except requests.exceptions.ConnectionError:
        return None, None, "Connection error: Could not connect to the backend service. Please check if the service is running."
    except requests.exceptions.RequestException as e:
        return None, None, f"Request error: {str(e)}"
    except Exception as e:
        return None, None, f"Unexpected error: {str(e)}"

# Function to handle language swap
def swap_languages():
    # Get current values
    current_source = st.session_state.source_language
    current_target = st.session_state.target_language
    
    # Swap languages
    st.session_state.source_lang = current_target
    st.session_state.target_lang = current_source
    
    # Swap text content
    if hasattr(st.session_state, 'translated_text') and st.session_state.translated_text:
        # Set the source text to be the previous translation result
        st.session_state.source_text = st.session_state.translated_text
        # Clear the translated text since we need to translate in the other direction
        st.session_state.translated_text = ""
    
    # Reload the page to reflect the changes
    st.experimental_rerun()

# App header
st.title("🌐 LLM Translator")
st.markdown("Translate text between languages using advanced LLM technology.")

# Check backend health on startup
backend_ok, backend_message = check_backend_health()
if not backend_ok:
    st.warning(f"⚠️ Warning: {backend_message}")
    if "API key not configured" in backend_message:
        st.error("The OpenRouter API key is not configured. Please add your API key to the .env file.")

# Create columns for language selection
col1, col2, col_button, col3 = st.columns([1, 1, 0.2, 1])

with col1:
    # Get source language from session state or use default
    default_source_idx = 0
    if 'source_lang' in st.session_state:
        default_source_idx = list(LANGUAGES.keys()).index(st.session_state.source_lang) \
            if st.session_state.source_lang in LANGUAGES else 0
    
    source_lang = st.selectbox("From", options=list(LANGUAGES.keys()), index=default_source_idx, key="source_language")

with col_button:
    st.write("")
    st.write("")
    if st.button("🔄", key="swap_button"):
        swap_languages()

with col3:
    # Get target language from session state or use default
    default_target_idx = 1
    if 'target_lang' in st.session_state:
        default_target_idx = list(LANGUAGES.keys()).index(st.session_state.target_lang) \
            if st.session_state.target_lang in LANGUAGES else 1
    
    target_lang = st.selectbox("To", options=list(LANGUAGES.keys()), index=default_target_idx, key="target_language")

# Text area for input - use session state to preserve text when swapping
source_text = st.text_area("Enter text to translate", 
                          value=st.session_state.source_text,
                          height=150, 
                          key="input_text")

# Update the source_text in session state when it changes
st.session_state.source_text = source_text

# Add progress container for better feedback
progress_container = st.empty()

# Container for translation result
result_container = st.container()

# Create a variable to store the translate button state
translate_button = st.button("Translate", key="translate_button")

# Translation button logic
if translate_button:
    if source_text:
        # Check for identical languages
        if source_lang == target_lang:
            st.warning("Source and target languages are the same. No translation needed.")
        else:
            # Show progress spinner with message
            with st.spinner("Translating..."):
                progress_container.info("Connecting to translation service...")
                time.sleep(0.5)  # Small delay for better UX
                
                # Check connection before proceeding
                backend_ok, backend_message = check_backend_health()
                if not backend_ok:
                    st.error(f"Translation service unavailable: {backend_message}")
                else:
                    progress_container.info("Performing translation... This may take a moment for longer texts.")
                    
                    # Perform translation
                    translated_text, model_used, error = translate_text(
                        source_text, 
                        LANGUAGES[source_lang],
                        LANGUAGES[target_lang]
                    )
                    
                    # Clear progress message
                    progress_container.empty()
                    
                    if translated_text:
                        st.success("Translation complete!")
                        
                        # Store the translated text in session state
                        st.session_state.translated_text = translated_text
                        
                        # Display translation result
                        with result_container:
                            st.text_area("Translation result", translated_text, height=150, key="output_text")
                            
                            # Display the model that was used for translation
                            if model_used:
                                model_name = model_used.split('/')[-1].split(':')[0]
                                st.info(f"Translation performed using: {model_name}")
                    elif error:
                        st.error(f"Translation failed: {error}")
                        if "API key" in error:
                            st.info("💡 Tip: Make sure you've set up the OpenRouter API key in the .env file.")
    else:
        st.warning("Please enter some text to translate.")

# Display previous translation result if it exists and no new translation was performed
if not translate_button and st.session_state.translated_text:
    with result_container:
        st.text_area("Translation result", st.session_state.translated_text, height=150, key="saved_output")
        
# Footer
st.markdown("---")
st.caption("Powered by LLM technology via OpenRouter.")