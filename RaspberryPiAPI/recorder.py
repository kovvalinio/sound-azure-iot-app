import os
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.exceptions import ResourceExistsError
from time import sleep
import socket
from datetime import datetime


HOST = "<ip>"
PORT = <port>


storage_connection_string = "<acces_token>"

if storage_connection_string is None:
    raise ValueError("Please set the AZURE_STORAGE_CONNECTION_STRING environment variable.")


blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)

container_id = "sounds"
target_blob_name = "file.wav"


def upload_file():
    blob_client = blob_service_client.get_blob_client(container=container_id, blob=target_blob_name)
    try:
        with open(target_blob_name, "rb") as file_data:
            blob_client.upload_blob(file_data, overwrite=False)
        print(f"File '{target_blob_name}' uploaded successfully to '{target_blob_name}' in container '{container_id}'.")
    except ResourceExistsError:
        print(f"Blob '{target_blob_name}' already exists in container '{container_id}'. Set 'overwrite=True' to replace it.")
    except FileNotFoundError:
        print(f"File '{target_blob_name}' not found. Please check the path and try again.")


def record_sample():
    global target_blob_name
    target_blob_name = f"sound_{datetime.now().strftime('%H-%M-%S')}_{datetime.now().strftime('%Y-%m-%d')}.wav"
    command = f"arecord -D plughw:0,0 --duration=3 -f cd " + target_blob_name
    os.system(command)


def listen():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f'Listening on {HOST}:{PORT}...')
        while True:
            conn, addr = server_socket.accept()
            with conn:
                print(f'Connected with {addr}')
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    print(f'Received data: {data.decode()}')
                    if data.decode() == 'record':
                        record_sample()
                    conn.sendall(b'uploading data...')
                    upload_file()
                    conn.sendall(b'done')


if __name__ == "__main__":
    listen()

