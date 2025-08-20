#!/usr/bin/env python3
"""
Admin app: quản lý mã code
- Tạo code (random), chọn loại (personal/shared)
- Chọn số ngày tồn tại
- Chọn mod được cấp quyền
- Xem danh sách code, trạng thái
- Xem chi tiết: máy/IP đã sử dụng
- Khoá / Mở khoá, Xoá code
- Tự động push codes.json lên GitHub
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json, os, datetime, random, string, csv, subprocess

CODES_FILE = "codes.json"
AVAILABLE_MODS = ["A: Pach Ultimate", "B: Classic 2016", "C: Classic League"]

# 🟢 Cấu hình GitHub Repo local
GIT_REPO_PATH = r"G:\FIFA_Launcher\admin"  
# 👉 thay bằng thư mục chứa file codes.json đã clone từ GitHub

def git_push():
    try:
        # chạy lệnh git trong repo
        subprocess.check_call(["git", "-C", GIT_REPO_PATH, "add", CODES_FILE])
        subprocess.check_call(["git", "-C", GIT_REPO_PATH, "commit", "-m", "Update codes.json"], stderr=subprocess.DEVNULL)
        subprocess.check_call(["git", "-C", GIT_REPO_PATH, "push"])
        print("✅ Đã push codes.json lên GitHub")
    except subprocess.CalledProcessError as e:
        messagebox.showwarning("Git Push", f"Không push được lên GitHub.\nChi tiết: {e}")

def load_codes():
    if os.path.exists(CODES_FILE):
        try:
            with open(CODES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_codes(codes):
    with open(CODES_FILE, "w", encoding="utf-8") as f:
        json.dump(codes, f, indent=4, ensure_ascii=False)
    # gọi git push sau khi lưu
    git_push()

def make_code(length=10):
    import string, random
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def days_left(expiry_str):
    try:
        exp = datetime.date.fromisoformat(expiry_str)
        return (exp - datetime.date.today()).days
    except:
        return -1

class AdminApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Admin - Code Manager")
        self.root.geometry("950x520")

        self.codes = load_codes()

        top = tk.Frame(root)
        top.pack(fill="x", padx=8, pady=6)

        # type
        tk.Label(top, text="Loại (personal/shared):").grid(row=0, column=0, sticky="w")
        self.type_var = tk.StringVar(value="personal")
        ttk.Combobox(top, textvariable=self.type_var, values=["personal","shared"], width=12).grid(row=0, column=1, padx=6)

        # days
        tk.Label(top, text="Số ngày tồn tại:").grid(row=0, column=2, sticky="w")
        self.days_entry = tk.Entry(top, width=8)
        self.days_entry.grid(row=0, column=3, padx=6)
        self.days_entry.insert(0, "30")

        # mods
        tk.Label(top, text="Chọn mod cho code:", anchor="w").grid(row=1, column=0, pady=(8,0), sticky="w")
        mods_frame = tk.Frame(top)
        mods_frame.grid(row=1, column=1, columnspan=4, sticky="w")
        self.mod_vars = {}
        for i, m in enumerate(AVAILABLE_MODS):
            v = tk.BooleanVar()
            cb = tk.Checkbutton(mods_frame, text=m, variable=v)
            cb.grid(row=0, column=i, padx=6)
            self.mod_vars[m] = v

        tk.Button(top, text="Tạo code ngẫu nhiên", command=self.create_code, bg="#2e7d32", fg="white").grid(row=0, column=4, padx=10)
        tk.Button(top, text="Export CSV", command=self.export_csv).grid(row=0, column=5, padx=6)

        # treeview
        cols = ("Code","Loại","Hết hạn","Mods","Trạng thái","Còn lại (ngày)","Máy/IP đã dùng")
        self.tree = ttk.Treeview(root, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=130 if c!="Mods" else 220)
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

        btn_frame = tk.Frame(root)
        btn_frame.pack(fill="x", padx=8, pady=6)
        tk.Button(btn_frame, text="Xem chi tiết", command=self.view_details).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Khóa/Mở khóa", command=self.toggle_lock).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Xóa code", command=self.delete_code).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Refresh", command=self.refresh).pack(side="left", padx=6)

        self.refresh()

    def create_code(self):
        days_text = self.days_entry.get().strip()
        if not days_text.isdigit():
            messagebox.showerror("Lỗi", "Số ngày phải là số nguyên dương.")
            return
        days = int(days_text)
        if days <= 0:
            messagebox.showerror("Lỗi", "Số ngày phải > 0.")
            return
        chosen_mods = [m.split(":")[0] for m,v in self.mod_vars.items() if v.get()]
        if not chosen_mods:
            messagebox.showerror("Lỗi", "Phải chọn ít nhất 1 mod.")
            return
        code = make_code(10)
        expiry = (datetime.date.today() + datetime.timedelta(days=days)).isoformat()
        codes = load_codes()
        codes[code] = {
            "type": self.type_var.get(),
            "expiry": expiry,
            "mods": chosen_mods,
            "locked": False,
            "machine_id": None,
            "ips": []
        }
        save_codes(codes)
        messagebox.showinfo("Tạo thành công", f"Đã tạo code: {code}\nHết hạn: {expiry}")
        self.refresh()

    def refresh(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        codes = load_codes()
        for code, info in codes.items():
            left = days_left(info.get("expiry","1970-01-01"))
            status = "Bị khóa" if info.get("locked", False) else "Hoạt động"
            used = info.get("machine_id") if info.get("type")=="personal" else ",".join(info.get("ips",[])) or "None"
            mods = ",".join(info.get("mods",[]))
            self.tree.insert("", "end", values=(code, info.get("type"), info.get("expiry"), mods, status, f"{left}", used))

    def get_selected_code(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Chú ý", "Chọn 1 code trong bảng trước.")
            return None
        return self.tree.item(sel[0])["values"][0]

    def view_details(self):
        code = self.get_selected_code()
        if not code: return
        codes = load_codes()
        info = codes.get(code, {})
        txt = f"Code: {code}\nLoại: {info.get('type')}\nHết hạn: {info.get('expiry')}\nMods: {','.join(info.get('mods',[]))}\nTrạng thái: {'Bị khóa' if info.get('locked') else 'Hoạt động'}\n"
        if info.get("type")=="personal":
            txt += f"Máy đã gắn (machine_id): {info.get('machine_id','Chưa có')}\n"
        txt += f"IPs đã dùng: {', '.join(info.get('ips',[])) or 'None'}"
        messagebox.showinfo("Chi tiết code", txt)

    def toggle_lock(self):
        code = self.get_selected_code()
        if not code: return
        codes = load_codes()
        if code in codes:
            codes[code]["locked"] = not codes[code].get("locked", False)
            save_codes(codes)
        self.refresh()

    def delete_code(self):
        code = self.get_selected_code()
        if not code: return
        if not messagebox.askyesno("Xác nhận", f"Xóa code {code}?"):
            return
        codes = load_codes()
        if code in codes:
            del codes[code]
            save_codes(codes)
        self.refresh()

    def export_csv(self):
        codes = load_codes()
        rows = []
        for code, info in codes.items():
            rows.append({
                "code": code,
                "type": info.get("type"),
                "expiry": info.get("expiry"),
                "mods": ";".join(info.get("mods",[])),
                "locked": info.get("locked", False),
                "machine_id": info.get("machine_id") or "",
                "ips": ";".join(info.get("ips",[]))
            })
        fname = "codes_export.csv"
        with open(fname, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["code","type","expiry","mods","locked","machine_id","ips"])
            writer.writeheader()
            writer.writerows(rows)
        messagebox.showinfo("Export", f"Đã xuất {fname}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AdminApp(root)
    root.mainloop()