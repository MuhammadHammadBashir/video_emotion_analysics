import streamlit as st
import os
import json
import requests
from azure.storage.blob import BlobServiceClient

def upload_file_to_folder(blob_service_client, container_name, folder_path, file_path):
    """
    Upload a file to a folder in Azure Blob Storage.

    Args:
        blob_service_client (BlobServiceClient): Blob service client.
        container_name (str): Name of the container.
        folder_path (str): Path of the folder (e.g., 'myfolder/subfolder/').
        file_path (str): Local file path to upload.

    Returns:
        str: URL of the uploaded blob or None if the upload failed.
    """
    try:
        file_name = os.path.basename(file_path)
        file_name = file_name.replace(" ", "_")
        blob_path = f"{folder_path}/{file_name}".strip("/")
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)

        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        return blob_client.url
    except Exception as e:
        st.error(f"Failed to upload file: {e}")
        return None

# Azure and Streamlit setup
CONNECT_STR = st.secrets["api_keys"]["azure"]
CONTAINER_NAME = 'emotionvideoanalysics'
BLOB_SERVICE_CLIENT = BlobServiceClient.from_connection_string(CONNECT_STR)

st.title("Emotion Analysis for Videos")

# API selection
api_options = {
    "Face + Caption": "https://api.cortex.cerebrium.ai/v4/p-c3473400/emotionanalysics2/run",
    "Face + HuggingfaceDS": "https://api.cortex.cerebrium.ai/v4/p-c3473400/emotionanalysics/run",
    "Caption": "https://api.cortex.cerebrium.ai/v4/p-c3473400/emotionanalysics3/run"
}
selected_api = st.selectbox("Select the API for analysis", list(api_options.keys()))

# File uploader
uploaded_file = st.file_uploader("Select a video file to upload", type=["mp4", "avi"])

folder_path = 'videos'
if uploaded_file:
    temp_file_path = os.path.join("temp", uploaded_file.name)
    os.makedirs("temp", exist_ok=True)
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.write(f"Selected file: {uploaded_file.name}")

    if st.button("Upload and Analyze"):
        st.info("Uploading file...")
        blob_url = upload_file_to_folder(BLOB_SERVICE_CLIENT, CONTAINER_NAME, folder_path, temp_file_path)

        if blob_url:
            st.success(f"File successfully uploaded to {folder_path}! Blob URL: {blob_url}")

            st.info("Processing the uploaded video for emotion analysis... This might take a few minutes.")
            with st.spinner("Analyzing emotions... Please wait."):
                url = api_options[selected_api]
                payload = json.dumps({'media_url': blob_url})
                headers = {
                    'Authorization': st.secrets["api_keys"]["cerebrium"],
                    'Content-Type': 'application/json'
                }

                try:
                    response = requests.post(url, headers=headers, data=payload, timeout=300)
                    response_data = response.json()

                    if "result" in response_data:
                        result = response_data["result"]
                        milli_seconds_spent = response_data["run_time_ms"]
                        seconds = (milli_seconds_spent / 1000) + 15
                        cost = seconds * 0.0007449
                        
                        result_video_path = result.get("result_video_path", "N/A")
                        combined_html_path = result.get("combined_html_path", "N/A")

                        st.success("Analysis completed successfully!")
                        st.markdown("### Key Results")

                        # Check if the result video path is available and display it in a video player
                        if result_video_path != "N/A":
                            st.markdown("#### Result Video")
                            st.markdown(f"- **Result Video download:** [{result_video_path}]({result_video_path})")
                        else:
                            st.markdown("- **Result Video Path:** N/A")
                        st.markdown("### Additional zip Results")
                        for key, value in result.items():
                            if key not in ["result_video_path", "combined_html_path"]:
                                st.markdown(f"- **{key.replace('_', ' ').capitalize()}:** [{value}]({value})")
                        st.markdown(f"### Total Time: **{seconds:.2f} seconds** | Cost Spent: **${cost:.2f}**")
                        if combined_html_path != "N/A":
                            st.markdown("#### Combined visualization Output")
                            st.markdown(f"Download: [Combined visualization]({combined_html_path})")
                            with st.spinner("Loading combined HTML content..."):
                                try:
                                    response = requests.get(combined_html_path, timeout=30)
                                    response.raise_for_status()
                                    html_content = response.text
                                    st.components.v1.html(html_content, width=1000, height=1000, scrolling=True)
                                except requests.exceptions.RequestException as e:
                                    st.error(f"Failed to load HTML content: {e}")
                        else:
                            st.markdown("- **Combined HTML Path:** N/A")
                    else:
                        st.error("Error: The API response did not contain expected results.")
                except requests.exceptions.RequestException as e:
                    st.error(f"API request failed: {e}")

        else:
            st.error("Failed to upload file.")

        os.remove(temp_file_path)
else:
    st.info("Please upload a video file (.mp4 or .avi).")
