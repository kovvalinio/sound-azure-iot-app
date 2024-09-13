import os
import tkinter as tk
from tkinter import ttk
from azure.storage.blob import BlobServiceClient
from tkinter import messagebox
import wave
import numpy as np
import matplotlib.pyplot as plt
import simpleaudio as sa
import speech_recognition as sr
import threading
import socket
from scipy import signal

storage_connection_string = "<acces_token>"
container_name = "sounds"

def set_status(status):
    status_text.set(f"Status: {status}")

def list_files_in_container():
    try:
        file_listbox.delete(0, tk.END)

        blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)
        container_client = blob_service_client.get_container_client(container_name)

        blob_list = container_client.list_blobs()

        for blob in blob_list:
            file_listbox.insert(tk.END, blob.name)

    except Exception as e:
        messagebox.showerror("Error", f"Could not upload the files: {e}")

def download_file_from_blob(blob_name):
    try:
        blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        
        with open(blob_name, "wb") as download_file:
            download_file.write(blob_client.download_blob().readall())
        
        return blob_name
    except Exception as e:
        set_status("idle")
        messagebox.showerror("Error", f"Could not download the file: {e}")

def upload_file_to_blob(file_path, blob_name):
    try:
        blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        
        set_status("idle")
    except Exception as e:
        set_status("idle")
        messagebox.showerror("Error", f"Could not upload the file: {e}")

def denoise_audio(file_path):
    try:
        with wave.open(file_path, 'r') as wav_file:
            params = wav_file.getparams()
            frames = wav_file.readframes(-1)
            sound_info = np.frombuffer(frames, dtype=np.int16)
            sample_rate = wav_file.getframerate()

            b, a = signal.butter(4, 0.1, 'low')
            denoised = signal.filtfilt(b, a, sound_info)

            denoised_file_path = f"denoised_{os.path.basename(file_path)}"
            with wave.open(denoised_file_path, 'w') as denoised_wav_file:
                denoised_wav_file.setparams(params)
                denoised_wav_file.writeframes(denoised.astype(np.int16).tobytes())
            
            return denoised_file_path
    except Exception as e:
        messagebox.showerror("Error", f"Could not denoise the file: {e}")

def show_waveform(blob_name):
    try:
        local_file_path = download_file_from_blob(blob_name)

        with wave.open(local_file_path, "r") as wav_file:
            frames = wav_file.readframes(-1)
            sound_info = np.frombuffer(frames, dtype=np.int16)
            frame_rate = wav_file.getframerate()

        time_axis = np.linspace(0, len(sound_info) / frame_rate, num=len(sound_info))
        plt.figure(figsize=(10, 4))
        plt.plot(time_axis, sound_info)
        plt.title(f"Waveform of {blob_name}")
        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude")
        plt.grid(True)

        plt.show()

    except Exception as e:
        messagebox.showerror("Error", f"Could not load the waveform: {e}")

def play_sound(blob_name):
    try:
        local_file_path = download_file_from_blob(blob_name)

        with wave.open(local_file_path, "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            num_channels = wav_file.getnchannels()
            sampwidth = wav_file.getsampwidth()
            frames = wav_file.readframes(-1)
            sound_data = np.frombuffer(frames, dtype=np.int16)

            if num_channels == 2:
                sound_data = np.reshape(sound_data, (-1, 2))
            elif num_channels != 1:
                raise ValueError("Only mono and stereo are supported")

            play_obj = sa.play_buffer(sound_data, num_channels, sampwidth, sample_rate)
            play_obj.wait_done()

    except Exception as e:
        messagebox.showerror("Error", f"Could not play the file: {e}")

def recognize_speech(blob_name):
    try:
        local_file_path = download_file_from_blob(blob_name)

        recognizer = sr.Recognizer()
        with sr.AudioFile(local_file_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language='pl-PL')

        result_window = tk.Toplevel(window)
        result_window.title("Recognized text")
        result_label = tk.Label(result_window, text=text, wraplength=400)
        result_label.pack(padx=10, pady=10)

    except Exception as e:
        messagebox.showerror("Error", f"Could not recognize the speech: {e}")

def on_right_click(event):
    try:
        selected_index = file_listbox.nearest(event.y)
        file_listbox.selection_clear(0, tk.END)
        file_listbox.selection_set(selected_index)
        selected_file = file_listbox.get(selected_index)
        
        context_menu.tk_popup(event.x_root, event.y_root)
    except Exception as e:
        messagebox.showerror("Error", f"Click error: {e}")

def denoise_audio_from_menu():
    try:
        selected_file = file_listbox.get(file_listbox.curselection())
        local_file_path = download_file_from_blob(selected_file)
        denoised_file_path = denoise_audio(local_file_path)
        denoised_blob_name = f"denoised_{selected_file}"
        upload_file_to_blob(denoised_file_path, denoised_blob_name)
        messagebox.showinfo("Info", f"File denoised and uploaded as {denoised_blob_name}")
    except Exception as e:
        messagebox.showerror("Error", f"Could not denoise the file: {e}")

def display_waveform_from_menu():
    try:
        selected_file = file_listbox.get(file_listbox.curselection())
        show_waveform(selected_file)
    except Exception as e:
        messagebox.showerror("Error", f"Could not display the waveform: {e}")

def play_sound_from_menu():
    try:
        selected_file = file_listbox.get(file_listbox.curselection())
        play_sound(selected_file)
    except Exception as e:
        messagebox.showerror("Error", f"Could not play the file: {e}")

def recognize_speech_from_menu():
    try:
        selected_file = file_listbox.get(file_listbox.curselection())
        recognize_speech(selected_file)
    except Exception as e:
        messagebox.showerror("Error", f"Could not recognize the speech: {e}")

def record_function():
    set_status("recording...")
    HOST = '<raspberry_ip>'
    PORT = <port> 
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((HOST, PORT))
            client_socket.sendall(b'record')
            data = client_socket.recv(1024)
            if data.decode() == "uploading data...":
                set_status("uploading...")
            data = client_socket.recv(1024) 
            if data.decode() == "done":
                set_status("idle")
                list_files_in_container()
    except Exception as e:
        set_status("idle")
        messagebox.showerror("Error", f"Could not record: {e}")

def run_in_thread(func, *args):
    threading.Thread(target=func, args=args, daemon=True).start()

window = tk.Tk()
window.title("Sound IoT App")

label = tk.Label(window, text="Waveforms available in the Azure cloud:")
label.pack(pady=10)

file_listbox = tk.Listbox(window, height=15, width=50)
file_listbox.pack(padx=20, pady=10)

context_menu = tk.Menu(window, tearoff=0)
context_menu.add_command(label="Display the waveform", command=display_waveform_from_menu)
context_menu.add_command(label="Play", command=play_sound_from_menu)
context_menu.add_command(label="Recognize speech", command=recognize_speech_from_menu)
context_menu.add_command(label="Denoise", command=denoise_audio_from_menu)

file_listbox.bind('<Button-3>', on_right_click)

refresh_button = tk.Button(window, text="Refresh", command=lambda: run_in_thread(list_files_in_container))
refresh_button.pack(side=tk.LEFT, pady=10)

record_button = tk.Button(window, text="Record", command=lambda: run_in_thread(record_function))
record_button.pack(side=tk.LEFT, pady=10)

status_text = tk.StringVar()
status_text.set("Status: idle")
status_label = tk.Label(window, textvariable=status_text)
status_label.pack(pady=10)
list_files_in_container()

window.mainloop()
