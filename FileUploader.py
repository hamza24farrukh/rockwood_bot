# uploads files to blob storage
import os
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv

load_dotenv(dotenv_path=r"C:\\Users\\Hasan\\OneDrive\\Desktop\\estrats\\workvenv\\Chatbot_integration\\settings.env") 


storage_account_name = os.getenv("Storage_Account")
storage_account_key = os.getenv("API_Key")
connection_string = f"DefaultEndpointsProtocol=https;AccountName={storage_account_name};AccountKey={storage_account_key};EndpointSuffix=core.windows.net"

blob_service_client = BlobServiceClient.from_connection_string(connection_string)

def list_all_containers():
    
    containers = blob_service_client.list_containers()

    for container in containers:
        print(container.name)

def create_container(container_name):

    blob_service_client.create_container(container_name)


def upload_blobs(container_name):
    container_client = blob_service_client.get_container_client(container_name)
    local_path = "./blobs"
    for file_name in os.listdir(local_path):
        print(f"Uploading file as blob: {file_name}")
        blob_client = container_client.get_blob_client(file_name)
        content_type = None
        if file_name.lower().endswith('.jpg') or file_name.lower().endswith('.jpeg'):
            content_type = 'image/jpeg'
        elif file_name.lower().endswith('.png'):
            content_type = 'image/png'
        
        if content_type is not None:
            with open(f"{local_path}/{file_name}", "rb") as data:
                blob_client.upload_blob(data, content_settings=ContentSettings(content_disposition='inline', content_type=content_type))

 
def show_uploaded_blobs(container_name):
    container_client = blob_service_client.get_container_client(container_name)
    
    for blobs in container_client.list_blobs():
        print("##################################################")
        print(blobs)

def show_blobs_links(storage_account, container_name):
    #https://STORAGEACCOUNT.blob.core.windows.net/CONTAINER/FILENAME

    container_client = blob_service_client.get_container_client(container_name)
    for blob in container_client.list_blobs():

        link = f"https://{storage_account}.blob.core.windows.net/{container_name}/{blob.name}"

        print(link)
        
def delete_all_blobs(container_name):
    container_client = blob_service_client.get_container_client(container_name)
    
    for blob in container_client.list_blobs():

        print(f"Deleting blob: {blob.name}")
        blob_client = container_client.get_blob_client(blob.name)
        blob_client.delete_blob()




delete_all_blobs('content-test-images')
#create_container("content-test-images")
#list_all_containers()

upload_blobs("content-test-images")
show_blobs_links("stoxb2qmiiznlsa","content-test-images")

#show_uploaded_blobs("content-test-images")

# blob_client = blob_service_client.get_blob_client("content-test-images", "test.png")
# props = blob_client.get_blob_properties()
# print(props)
# props.content_settings.content_disposition = "inline; filename=test.jpeg"
# blob_client.set_http_headers(props.content_settings)