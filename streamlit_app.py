import streamlit as st
import openai
import boto3
from openai import OpenAI
from PIL import Image as PILImage
from io import BytesIO

# Load API key from Streamlit secrets
openai.api_key = st.secrets["openai"]["api_key"]
MODEL = "gpt-4o"

# Initialize S3 client with credentials from Streamlit secrets
s3_client = boto3.client(
    's3',
    aws_access_key_id=st.secrets["aws"]["access_key_id"],
    aws_secret_access_key=st.secrets["aws"]["secret_access_key"]
)
client = OpenAI(api_key=openai.api_key)
bucket_name = 'gpt4o-funtest'

# Streamlit UI components
st.title("Math Helper Chatbot")

# Initialize session state for image URL
if 's3_image_url' not in st.session_state:
    st.session_state['s3_image_url'] = None

# Image uploader
uploaded_image = st.file_uploader("Upload an image with a math problem", type=["jpg", "jpeg", "png"], key='image_uploader')
if uploaded_image:
    # Display the uploaded image
    image = PILImage.open(uploaded_image)
    st.image(image, caption='Uploaded Image')

    # Upload image to S3 and get URL
    object_name = uploaded_image.name
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    try:
        s3_client.upload_fileobj(buffer, bucket_name, object_name)
        st.session_state['s3_image_url'] = f"https://{bucket_name}.s3.amazonaws.com/{object_name}"
    except Exception as e:
        st.error(f"Failed to upload image to S3: {str(e)}")

# Ensure unique keys for user input to avoid DuplicateWidgetID error
if 'input_key' not in st.session_state:
    st.session_state['input_key'] = 0

user_input = st.text_input("Ask a math question or type 'exit' to stop:", key=f'input_{st.session_state.input_key}')

if st.button("Send", key='send_button'):
    if user_input.lower() == "exit":
        st.stop()
    elif user_input:
        # Increment the key for the next input
        st.session_state['input_key'] += 1

        # API call to OpenAI with user input and image
        if st.session_state['s3_image_url']:
            completion = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that responds in Markdown. Help me with my math homework!"},
                    {"role": "user", "content": [
                        {"type": "text", "text": user_input},
                        {"type": "image_url", "image_url": {"url": st.session_state['s3_image_url']}}
                    ]}
                ],
                temperature=0.0,
            )
            
            # Display the response in a chat box using Markdown
            if completion:
                response = completion.choices[0].message.content
                st.markdown(f"**Assistant:**\n{response}", unsafe_allow_html=True)

