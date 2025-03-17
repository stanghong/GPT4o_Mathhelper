import streamlit as st
import openai
import boto3
import base64
from PIL import Image as PILImage
from io import BytesIO

# Load API keys from Streamlit secrets
openai.api_key = st.secrets["openai"]["api_key"]
MODEL = "gpt-4o"

# Initialize OpenAI client
client = OpenAI(api_key=openai.api_key)

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

if 'image_data' not in st.session_state:
    st.session_state['image_data'] = None

# Upload Image
uploaded_image = st.file_uploader("Upload an image with a math problem", type=["jpg", "jpeg", "png"], key='image_uploader')

if uploaded_image:
    image = PILImage.open(uploaded_image)
    st.image(image, caption='Uploaded Image')

    # Convert image to base64 for OpenAI processing
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    # Store image data for later use
    st.session_state['image_data'] = encoded_image

    # Upload image to S3
    object_name = uploaded_image.name
    try:
        s3_client.upload_fileobj(buffer, bucket_name, object_name)
        st.session_state['s3_image_url'] = f"https://{bucket_name}.s3.amazonaws.com/{object_name}"
        st.success(f"Image uploaded successfully! URL: {st.session_state['s3_image_url']}")
    except Exception as e:
        st.error(f"Failed to upload image to S3: {str(e)}")

if 'input_key' not in st.session_state:
    st.session_state['input_key'] = 0

# Text Input
user_input = st.text_input("Ask a math question or type 'exit' to stop:", key=f'input_{st.session_state.input_key}')

if st.button("Send", key='send_button'):
    if user_input.lower() == "exit":
        st.stop()
    elif user_input or st.session_state['image_data']:
        st.session_state['input_key'] += 1

        messages = [{"role": "system", "content": "You are a helpful assistant that solves math problems."}]

        if user_input:
            messages.append({"role": "user", "content": user_input})

        if st.session_state['image_data']:
            messages.append(
                {"role": "user", "content": [
                    {"type": "text", "text": "Solve this math problem:"},
                    {"type": "image", "image": st.session_state['image_data']}
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
            st.error(f"OpenAI API error: {str(e)}")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
