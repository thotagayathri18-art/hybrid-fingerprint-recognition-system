import tkinter as tk
from tkinter import messagebox
import subprocess

# Hardcoded credentials (for now)
USERNAME = "admin"
PASSWORD = "1234"

def check_login():

    user = username_entry.get()
    pwd = password_entry.get()

    if user == USERNAME and pwd == PASSWORD:
        messagebox.showinfo("Login Success", "Welcome!")

        root.destroy()

        # Open GUI after login
        subprocess.run(["python", "gui.py"])

    else:
        messagebox.showerror("Login Failed", "Invalid credentials")


root = tk.Tk()
root.title("Fingerprint System Login")
root.geometry("300x200")

tk.Label(root, text="Login System", font=("Arial", 14, "bold")).pack(pady=10)

tk.Label(root, text="Username").pack()
username_entry = tk.Entry(root)
username_entry.pack()

tk.Label(root, text="Password").pack()
password_entry = tk.Entry(root, show="*")
password_entry.pack()

tk.Button(root, text="Login", command=check_login).pack(pady=10)

root.mainloop()