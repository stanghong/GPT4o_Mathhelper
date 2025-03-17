import streamlit as st
import openai
import boto3
import base64
from PIL import Image as PILImage
from io import BytesIO

# Load API key from Streamlit secrets
MODEL = "gpt-4o"

# ✅ Ensure OpenAI API key is used
if "openai" not in st.secrets or "api_key" not in st.secrets["openai"]:
    st.error("⚠️ OpenAI API key is missing! Add it in Streamlit Secrets.")
    st.stop()

# Initialize OpenAI client (Fixed)
client = openai.OpenAI(api_key=st.secrets["openai"]["api_key"])

# Initialize S3 client with credentials from Streamlit secrets
if "aws" not in st.secrets or "access_key_id" not in st.secrets["aws"] or "secret_access_key" not in st.secrets["aws"]:
    st.error("⚠️ AWS credentials are missing! Add them in Streamlit Secrets.")
    st.stop()

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
        st.success(f"✅ Image uploaded successfully! URL: {st.session_state['s3_image_url']}")
    except Exception as e:
        st.error(f"❌ Failed to upload image to S3: {str(e)}")

if 'input_key' not in st.session_state:
    st.session_state['input_key'] = 0

user_input = st.text_input("Ask a math question or type 'exit' to stop:", key=f'input_{st.session_state.input_key}')

if st.button("Send", key='send_button'):
    if user_input.lower() == "exit":
        st.stop()
    elif user_input or st.session_state['s3_image_url']:
        st.session_state['input_key'] += 1

        messages = [{"role": "system", "content": "You are a helpful assistant that solves math problems."}]

        if user_input:
            messages.append({"role": "user", "content": user_input})

        if st.session_state['s3_image_url']:
            messages.append(
                {"role": "user", "content": [
                    {"type": "text", "text": "Solve this math problem:"},
                    {"type": "image_url", "image_url": {"url": st.session_state['s3_image_url']}}
                ]}
            )

        try:
            completion = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.0,
            )

            if completion:
                response = completion.choices[0].message.content
                st.markdown(f"**Assistant:**\n{response}", unsafe_allow_html=True)

        except openai.OpenAIError as e:
            st.error(f"❌ OpenAI API error: {str(e)}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
