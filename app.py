import streamlit as st
import os
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
        # Extract the file name from the local file path
        file_name = os.path.basename(file_path)

        # Construct the blob path with the folder structure
        blob_path = f"{folder_path}/{file_name}".strip("/")

        # Get the blob client
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)

        # Upload the file
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        print(f"File uploaded to: {blob_client.url}")
        return blob_client.url
    except Exception as e:
        print(f"Failed to upload file: {e}")
        return None

CONNECT_STR = st.secrets["api_keys"]["azure"]
CONTAINER_NAME = 'emotionvideoanalysics'
BLOB_SERVICE_CLIENT = BlobServiceClient.from_connection_string(CONNECT_STR)

# Streamlit application
st.title("Upload Videos to Azure Blob Storage")

# File uploader
uploaded_file = st.file_uploader("Select a video file to upload", type=["mp4", "avi"])

# Folder path input
# folder_path = st.text_input("Enter the folder path in Azure Blob Storage (e.g., 'videos/subfolder')", value="videos")
folder_path = 'videos'
if uploaded_file:
    # Save the uploaded file temporarily
    temp_file_path = os.path.join("temp", uploaded_file.name)
    os.makedirs("temp", exist_ok=True)
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.write(f"Selected file: {uploaded_file.name}")

    # Upload button
    if st.button("Upload for analysics"):
        st.info("Uploading file...")

        # Upload file to Azure Blob Storage
        blob_url = upload_file_to_folder(BLOB_SERVICE_CLIENT, CONTAINER_NAME, folder_path, temp_file_path)

        if blob_url:
            st.success(f"File successfully uploaded to {folder_path}! Blob URL: {blob_url}")
        else:
            st.error("Failed to upload file.")

        # Cleanup temporary file
        os.remove(temp_file_path)
else:
    st.info("Please upload a video file (.mp4 or .avi).")
