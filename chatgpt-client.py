import os
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image, ImageTk
import requests
from io import BytesIO
import json


class ClientUI:
    def __init__(self, server_addr, server_port):
        self.root = tk.Tk()
        self.root.geometry("800x600")
        self.root.title("ChatGPT Client")
        self.server_addr = server_addr
        self.server_port = server_port
        self.messages_frame = tk.Frame(self.root)
        self.my_msg = tk.StringVar()
        self.my_msg.set("")
        self.scrollbar = tk.Scrollbar(self.messages_frame)
        self.msg_list = tk.Listbox(self.messages_frame, height=30, width=100, yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.msg_list.pack(side=tk.LEFT, fill=tk.BOTH)
        self.msg_list.pack()
        self.messages_frame.pack()
        self.entry_field = tk.Entry(self.root, textvariable=self.my_msg)
        self.entry_field.bind("<Return>", self.send_msg)
        self.entry_field.pack()
        self.send_button = tk.Button(self.root, text="Send", command=self.send_msg)
        self.send_button.pack()
        self.upload_button = tk.Button(self.root, text="Upload", command=self.upload_file)
        self.upload_button.pack()
        self.image_label = tk.Label(self.root)
        self.image_label.pack()
        self.current_file = None
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.iconify()
        threading.Thread(target=self.receive_msg).start()
        self.root.mainloop()

    def send_msg(self, event=None):
        msg = self.my_msg.get()
        self.my_msg.set("")
        if self.current_file is not None:
            self.send_file(msg)
            return
        try:
            requests.post(f"http://{self.server_addr}:{self.server_port}/msg", data=msg)
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Failed to connect to the server.")

    def receive_msg(self):
        while True:
            try:
                response = requests.get(f"http://{self.server_addr}:{self.server_port}/msg")
                if response.status_code == 200:
                    data = response.json()
                    if "msg" in data:
                        self.msg_list.insert(tk.END, data["msg"])
                    if "file" in data:
                        self.display_file(data["file"])
            except requests.exceptions.RequestException:
                messagebox.showerror("Error", "Failed to connect to the server.")
            time.sleep(0.1)

    def upload_file(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        self.current_file = file_path
        self.my_msg.set(f"Uploading {os.path.basename(file_path)}...")
        self.upload_button.config(state=tk.DISABLED)
        self.entry_field.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        threading.Thread(target=self.upload_file_thread, args=(file_path,)).start()

    def upload_file_thread(self, file_path):
        try:
            with open(file_path, "rb") as f:
                response = requests.post(f"http://{self.server_addr}:{self.server_port}/upload", files={"file": f})
                if response.status_code == 200:
                    self.my_msg.set(f"Uploaded {os.path.basename(file_path)}
