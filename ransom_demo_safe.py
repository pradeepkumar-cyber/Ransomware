"""
ransom_demo_safe.py
SAFE, NON-DESTRUCTIVE educational ransomware demo — self-contained (no pip installs).

Features:
- Runs with Python standard library only (Tkinter).
- Theme selector: Hacker (green), Red Alert, Classic.
- Blinking warning toggle.
- Fake countdown timer (configurable minutes).
- Fake QR placeholder drawn with Canvas (no external libs).
- Encrypts/decrypts demo copies only (original files untouched).
- User-friendly GUI with grouped frames, bigger buttons, and status bar.
- Useful for classroom/case-study demos. Do NOT use on important folders.
"""

import os
import random
import string
import hashlib
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

LOCK_SUFFIX = ".locked.demo"
NOTE_FILENAME = "README_DEMO_DECRYPT.txt"
APP_NAME = "Ransom-Demo (SAFE, Self-contained)"


def generate_unlock_code(length=12):
    chars = string.ascii_uppercase + string.digits
    return "DEMO-" + "".join(random.choice(chars) for _ in range(length))


def keystream(key: str, length: int) -> bytes:
    out = bytearray()
    counter = 0
    key_bytes = key.encode()
    while len(out) < length:
        h = hashlib.sha256(key_bytes + counter.to_bytes(8, "little")).digest()
        out.extend(h)
        counter += 1
    return bytes(out[:length])


def xor_encrypt(data: bytes, key: str) -> bytes:
    ks = keystream(key, len(data))
    return bytes(a ^ b for a, b in zip(data, ks))


def write_demo_note(folder: Path, unlock_code: str):
    note = f"""
###############################
#   RANSOMWARE DEMO — EDUCATIONAL
###############################

This is a SAFE demo for educational purposes only.

Files in this folder that have the extension "{LOCK_SUFFIX}" are encrypted *copies* created by this demo.
The original files are NOT modified or deleted.

To restore the demo copies, enter the unlock code shown in the application.

UNLOCK CODE: {unlock_code}

This repository/demo is for research and teaching only.
"""
    (folder / NOTE_FILENAME).write_text(note, encoding="utf-8")


def process_files_demo(folder: Path, key: str, encrypt=True):
    for p in folder.iterdir():
        if p.is_file():
            if p.name == NOTE_FILENAME:
                continue
            if encrypt:
                if p.name.endswith(LOCK_SUFFIX):
                    continue
                try:
                    data = p.read_bytes()
                    enc = xor_encrypt(data, key)
                    out_path = p.with_name(p.name + LOCK_SUFFIX)
                    out_path.write_bytes(enc)
                except Exception as e:
                    print(f"[!] Error encrypting {p.name}: {e}")
            else:
                if p.name.endswith(LOCK_SUFFIX):
                    try:
                        data = p.read_bytes()
                        dec = xor_encrypt(data, key)
                        restored_name = p.name[:-len(LOCK_SUFFIX)] + ".restored.demo"
                        out_path = folder / restored_name
                        out_path.write_bytes(dec)
                    except Exception as e:
                        print(f"[!] Error decrypting {p.name}: {e}")


def create_sample_files(folder: Path, count=3):
    for i in range(1, count + 1):
        f = folder / f"sample_file_{i}.txt"
        if not f.exists():
            f.write_text(f"This is sample file {i} for the ransomware demo.\n", encoding="utf-8")


def qr_placeholder_canvas(canvas, data: str, size: int = 220, margin: int = 8):
    """
    Draws a simple QR-like placeholder on the canvas based on hash of 'data'.
    Purely visual — NOT a real QR code.
    """
    canvas.delete("all")
    canvas.configure(width=size, height=size)
    grid = 21
    block = (size - margin * 2) / grid
    hv = hashlib.sha256(data.encode()).digest()
    bits = []
    for b in hv:
        for i in range(8):
            bits.append((b >> i) & 1)
    idx = 0
    for y in range(grid):
        for x in range(grid):
            v = bits[idx % len(bits)]
            color = "black" if v else "white"
            x0 = margin + x * block
            y0 = margin + y * block
            x1 = x0 + block
            y1 = y0 + block
            canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=color)
            idx += 1


# UI theme definitions
THEMES = {
    "Hacker (Green-on-Black)": {
        "bg": "#000000",
        "fg": "#00FF00",
        "alert": "#FF3300",
        "alert_alt": "#FFFF00",
        "button_bg": "#002200",
        "button_fg": "#00FF00",
        "entry_bg": "#001100",
        "entry_fg": "#00FF00",
    },
    "Red Alert": {
        "bg": "#000000",
        "fg": "#FFDD55",
        "alert": "#FF2E2E",
        "alert_alt": "#FFFFFF",
        "button_bg": "#220000",
        "button_fg": "#FFDD55",
        "entry_bg": "#110000",
        "entry_fg": "#FFDD55",
    },
    "Classic (Black/White)": {
        "bg": "#000000",
        "fg": "#FFFFFF",
        "alert": "#FF4444",
        "alert_alt": "#FFFF66",
        "button_bg": "#222222",
        "button_fg": "#FFFFFF",
        "entry_bg": "#111111",
        "entry_fg": "#FFFFFF",
    },
}


class DemoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1000x640")
        self.unlock_code = generate_unlock_code()
        print(f"[INFO] Unlock code: {self.unlock_code}")

        # UI state
        self.selected_dir = tk.StringVar()
        self.theme_name = tk.StringVar(value=list(THEMES.keys())[0])
        self.blink_enabled = tk.BooleanVar(value=True)
        self.countdown_minutes = tk.IntVar(value=59)
        self.show_unlock = tk.BooleanVar(value=False)

        # Build UI
        self.build_main_ui()
        self.apply_theme()

    def build_main_ui(self):
        # Title
        header = tk.Label(self.root, text=APP_NAME, font=("Consolas", 20, "bold"))
        header.pack(pady=(10, 6))

        # --- Directory Selection ---
        dir_frame = tk.LabelFrame(self.root, text="📂 Demo Directory", padx=10, pady=10)
        dir_frame.pack(fill="x", padx=12, pady=6)

        tk.Entry(dir_frame, textvariable=self.selected_dir, width=60).pack(side="left", padx=6)
        tk.Button(dir_frame, text="Browse...", command=self.choose_dir, width=12).pack(side="left")

        # --- Actions ---
        action_frame = tk.LabelFrame(self.root, text="🔧 Actions", padx=10, pady=10)
        action_frame.pack(fill="x", padx=12, pady=6)

        tk.Button(action_frame, text="📝 Prepare Demo", command=self.prepare_demo, width=22).pack(side="left", padx=8, pady=4)
        tk.Button(action_frame, text="🔒 Encrypt Copies", command=self.simulate_encrypt, width=22).pack(side="left", padx=8, pady=4)
        tk.Button(action_frame, text="🔓 Decrypt Copies", command=self.simulate_decrypt, width=22).pack(side="left", padx=8, pady=4)
        tk.Button(action_frame, text="⚠️ Show Ransom Screen", command=self.popup_ransom, width=22).pack(side="left", padx=8, pady=4)

        # --- Options ---
        opts_frame = tk.LabelFrame(self.root, text="⚙ Options", padx=10, pady=10)
        opts_frame.pack(fill="x", padx=12, pady=6)

        tk.Checkbutton(opts_frame, text="Blinking Warning", variable=self.blink_enabled).pack(side="left", padx=8)
        tk.Checkbutton(opts_frame, text="Show Unlock Code in main UI", variable=self.show_unlock).pack(side="left", padx=8)
        tk.Label(opts_frame, text="Countdown minutes:", font=("Consolas", 10)).pack(side="left", padx=(20, 6))
        tk.Spinbox(opts_frame, from_=0, to=999, width=5, textvariable=self.countdown_minutes).pack(side="left")

        tk.Label(opts_frame, text="Theme:", font=("Consolas", 10)).pack(side="left", padx=(20, 4))
        theme_menu = ttk.OptionMenu(opts_frame, self.theme_name, self.theme_name.get(), *THEMES.keys(), command=lambda e: self.apply_theme())
        theme_menu.pack(side="left")

        # --- Log ---
        self.log = tk.Text(self.root, height=12)
        self.log.pack(fill="both", expand=False, padx=12, pady=(6, 6))
        self.log_insert("Ready. Select a demo directory (create a new empty folder for safety).\n")

        # --- Status bar ---
        self.status_label = tk.Label(self.root, text=f"Unlock code: {self.unlock_code if self.show_unlock.get() else 'Hidden (enable display)'}", anchor="w", font=("Consolas", 10))
        self.status_label.pack(fill="x", padx=12, pady=(0, 10))

        def toggle_show(*_):
            self.status_label.config(text=f"Unlock code: {self.unlock_code if self.show_unlock.get() else 'Hidden (enable display)'}")
        self.show_unlock.trace_add("write", toggle_show)

    def apply_theme(self):
        t = THEMES.get(self.theme_name.get(), THEMES[list(THEMES.keys())[0]])
        bg = t["bg"]
        fg = t["fg"]
        btn_bg = t["button_bg"]
        btn_fg = t["button_fg"]
        entry_bg = t["entry_bg"]
        entry_fg = t["entry_fg"]

        self.root.configure(bg=bg)

        def recurse(widget):
            try:
                widget_type = widget.winfo_class()
            except Exception:
                widget_type = ""
            if widget_type in ("Frame", "Labelframe"):
                try:
                    widget.configure(bg=bg)
                except Exception:
                    pass
            elif widget_type in ("Label", "Button", "Checkbutton"):
                try:
                    widget.configure(bg=bg, fg=fg)
                except Exception:
                    pass
            elif widget_type in ("Entry", "Text", "Spinbox"):
                try:
                    widget.configure(bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
                except Exception:
                    pass
            for child in widget.winfo_children():
                recurse(child)
        recurse(self.root)
        self.status_label.configure(fg=fg, bg=bg)

    def choose_dir(self):
        d = filedialog.askdirectory(title="Choose Demo Directory")
        if d:
            self.selected_dir.set(d)

    def prepare_demo(self):
        folder = Path(self.selected_dir.get())
        if not folder.exists():
            messagebox.showerror("Error", "Please select or create a directory first.")
            return
        create_sample_files(folder)
        self.log_insert("[Demo] Sample files created.\n")

    def simulate_encrypt(self):
        folder = Path(self.selected_dir.get())
        if not folder.exists() or not folder.is_dir():
            messagebox.showerror("Error", "Invalid directory")
            return
        write_demo_note(folder, self.unlock_code)
        process_files_demo(folder, self.unlock_code, encrypt=True)
        self.log_insert("[Demo] Encrypted copies written with suffix: " + LOCK_SUFFIX + "\n")

    def simulate_decrypt(self):
        folder = Path(self.selected_dir.get())
        if not folder.exists() or not folder.is_dir():
            messagebox.showerror("Error", "Invalid directory")
            return
        process_files_demo(folder, self.unlock_code, encrypt=False)
        note = folder / NOTE_FILENAME
        if note.exists():
            note.unlink()
        self.log_insert("[Demo] Decrypted copies written as .restored.demo and demo note removed.\n")

    def popup_ransom(self):
        top = tk.Toplevel(self.root)
        top.attributes("-fullscreen", True)
        t = THEMES.get(self.theme_name.get(), THEMES[list(THEMES.keys())[0]])
        top.configure(bg=t["bg"])
        top.bind_all("<Control-Shift-q>", lambda e: top.destroy())
        top.title("⚠️ RANSOMWARE DEMO — Educational Only ⚠️")

        # blinking warning
        warning = tk.Label(top, text="!!! YOUR FILES ARE LOCKED !!!", fg=t["alert"], bg=t["bg"], font=("Consolas", 44, "bold"))
        warning.pack(pady=12)
        def blink():
            if self.blink_enabled.get():
                current_color = warning.cget("fg")
                new = t["alert_alt"] if current_color == t["alert"] else t["alert"]
                warning.config(fg=new)
            else:
                warning.config(fg=t["alert"])
            top.after(500, blink)
        blink()

        countdown_var = tk.StringVar(value=f"Time Left: {self.countdown_minutes.get():02}:00:00")
        countdown_lbl = tk.Label(top, textvariable=countdown_var, fg=t["fg"], bg=t["bg"], font=("Consolas", 20, "bold"))
        countdown_lbl.pack(pady=6)

        # countdown logic
        def start_fake_timer(total_minutes):
            total_seconds = max(0, int(total_minutes) * 60)
            def tick():
                nonlocal total_seconds
                hrs = total_seconds // 3600
                mins = (total_seconds % 3600) // 60
                secs = total_seconds % 60
                countdown_var.set(f"Time Left: {hrs:02}:{mins:02}:{secs:02}")
                if total_seconds > 0:
                    total_seconds -= 1
                    top.after(1000, tick)
            tick()
        start_fake_timer(self.countdown_minutes.get())

        frame = tk.Frame(top, bg=t["bg"], highlightbackground=t["alert"], highlightthickness=3, padx=18, pady=18)
        frame.pack(pady=18, padx=80, fill="x")

        msg = (
            "⚠️ THIS IS A SAFE EDUCATIONAL DEMO ⚠️\n\n"
            "Files ending with '.locked.demo' are encrypted COPIES only.\n"
            "Your original files are untouched.\n\n"
            "Enter the UNLOCK CODE below to restore.\n\n"
            "Press Ctrl+Shift+Q anytime to exit this screen."
        )
        tk.Label(frame, text=msg, fg=t["fg"], bg=t["bg"], font=("Consolas", 14), justify="center").pack(pady=(0, 12))

        # Payment demo placeholder
        pay_frame = tk.Frame(frame, bg=t["bg"])
        pay_frame.pack(pady=6)
        demo_addr = "DEMO-ADDRESS-DO-NOT-PAY-123456"
        tk.Label(pay_frame, text="DEMO PAYMENT (DO NOT PAY)", fg=t["fg"], bg=t["bg"], font=("Consolas", 11, "bold")).pack()
        addr_entry = tk.Entry(pay_frame, width=56, justify="center", font=("Consolas", 11))
        addr_entry.insert(0, demo_addr)
        addr_entry.configure(state="readonly", readonlybackground=t["entry_bg"], fg=t["entry_fg"])
        addr_entry.pack(pady=6)

        canvas = tk.Canvas(pay_frame, width=220, height=220, highlightthickness=0, bg=t["bg"])
        canvas.pack(pady=6)
        qr_placeholder_canvas(canvas, demo_addr, size=220, margin=8)

        def copy_addr():
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(demo_addr)
                messagebox.showinfo("Copied", "Demo address copied to clipboard (DEMO ONLY).")
            except Exception as e:
                messagebox.showerror("Error", f"Clipboard failed: {e}")
        tk.Button(pay_frame, text="Copy Demo Address", command=copy_addr, bg=t["button_bg"], fg=t["button_fg"]).pack(pady=6)

        # Unlock entry
        code_var = tk.StringVar()
        entry = tk.Entry(frame, textvariable=code_var, font=("Consolas", 18), justify="center", fg=t["entry_fg"], bg=t["entry_bg"], insertbackground=t["entry_fg"])
        entry.pack(pady=12)
        entry.focus()

        result = tk.Label(frame, text="", fg=t["fg"], bg=t["bg"], font=("Consolas", 14))
        result.pack(pady=(4, 10))

        def try_unlock():
            if code_var.get().strip() == self.unlock_code:
                result.config(text="✅ Correct code. Decrypting demo copies...", fg="#00DD00")
                self.simulate_decrypt()
                top.destroy()
            else:
                result.config(text="❌ Incorrect code. Try again.", fg=t["alert"])
        tk.Button(frame, text="Unlock", command=try_unlock, font=("Consolas", 14), bg=t["button_bg"], fg=t["button_fg"]).pack(pady=6)

        def close_popup():
            if messagebox.askyesno("Exit Demo", "Close the demo ransom screen? (This is safe)"):
                top.destroy()
        tk.Button(frame, text="Close Demo Screen (Safe)", command=close_popup, font=("Consolas", 11), bg=t["button_bg"], fg=t["button_fg"]).pack(pady=(8, 4))

    def log_insert(self, text):
        self.log.insert("end", text)
        self.log.see("end")


def main():
    root = tk.Tk()
    app = DemoGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
