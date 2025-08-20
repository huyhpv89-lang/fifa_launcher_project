import tkinter as tk
from tkinter import messagebox
import json, subprocess, datetime

CODES_FILE = "codes.json"

def save_codes(codes):
    with open(CODES_FILE, "w") as f:
        json.dump(codes, f, indent=4)

def git_push():
    try:
        subprocess.run(["git", "add", "."], check=True)
        commit_message = f"Update codes.json at {datetime.datetime.now()}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        messagebox.showinfo("Success", "✅ Đã lưu và push lên GitHub!")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"❌ Lỗi push Git: {e}")

def save_only():
    # ví dụ: ở đây mình test với dummy data
    codes = {"demo": {"type": "personal", "mods": ["mod1"], "days": 30}}
    save_codes(codes)
    messagebox.showinfo("Saved", "✅ Đã lưu codes.json cục bộ")

def save_and_push():
    codes = {"demo": {"type": "personal", "mods": ["mod1"], "days": 30}}
    save_codes(codes)
    git_push()

root = tk.Tk()
root.title("Admin App")

btn1 = tk.Button(root, text="💾 Save", command=save_only)
btn1.pack(pady=10)

btn2 = tk.Button(root, text="☁ Save & Push", command=save_and_push)
btn2.pack(pady=10)

root.mainloop()