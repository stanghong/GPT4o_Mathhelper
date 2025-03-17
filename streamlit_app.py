import streamlit as st
import openai
import boto3
import base64
from PIL import Image as PILImage
from io import BytesIO

# Load API keys from Streamlit secrets
openai.api_key = st.secrets["openai"]["api_key"]
MODEL = "gpt-4o"

# Initialize OpenAI client (Fixed)
client = openai.OpenAI()

# Initialize S3 client with credentials from Streamlit secrets
s3_client = boto3.client(
    's3',
    aws_access_key_id=st.secrets["aws"]["access_key_id"],
    aws_secret_access_key=st.secrets["aws"]["secret_access_key"]
)

bucket_name = 'gpt4o-fun-test'

st.title("Math Helper Chatbot")

# Initialize session state for image storage
if 's3_image_url' not in st.session_state:
    st.session_state['s3_image_url'] = None

uploaded_image = st.file_uploader("Upload an image with a math problem", type=["jpg", "jpeg", "png"], key='image_uploader')

if uploaded_image:
    image = PILImage.open(uploaded_image)
    st.image(image, caption='Uploaded Image')

    # Upload image to S3 and get URL
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    object_name = uploaded_image.name
    try:
        s3_client.upload_fileobj(buffer, bucket_name, object_name)
        st.session_state['s3_image_url'] = f"https://{bucket_name}.s3.amazonaws.com/{object_name}"
        st.success(f"Image uploaded successfully! URL: {st.session_state['s3_image_url']}")
    except Exception as e:
        st.error(f"Failed to upload image to S3: {str(e)}")

if 'input_key' not in st.session_state:
    st.session_state['input_key'] = 0
