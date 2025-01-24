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
                url = "https://api.cortex.cerebrium.ai/v4/p-c3473400/emotionanalysics/run"
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
                        result_video_path = result.get("result_video_path", "N/A")
                        combined_html_path = result.get("combined_html_path", "N/A")

                        st.success("Analysis completed successfully!")
                        st.markdown("### Key Results")
                        st.markdown(f"- **Result Video Path:** [{result_video_path}]({result_video_path})" if result_video_path != "N/A" else "- **Result Video Path:** N/A")
                        st.markdown(f"- **Combined HTML Path:** [{combined_html_path}]({combined_html_path})" if combined_html_path != "N/A" else "- **Combined HTML Path:** N/A")

                        st.markdown("### Additional Results")
                        for key, value in result.items():
                            if key not in ["result_video_path", "combined_html_path"]:
                                st.markdown(f"- **{key.replace('_', ' ').capitalize()}:** [{value}]({value})")
                    else:
                        st.error("Error: The API response did not contain expected results.")

                except requests.exceptions.RequestException as e:
                    st.error(f"API request failed: {e}")

        else:
            st.error("Failed to upload file.")

        os.remove(temp_file_path)
else:
    st.info("Please upload a video file (.mp4 or .avi).")
