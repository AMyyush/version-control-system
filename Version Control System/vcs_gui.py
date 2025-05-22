import customtkinter as ctk
from tkinter import messagebox
import os
import subprocess

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

REPO_NAME = "MyRepo"

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return "", str(e)

def init_repo():
    out, err = run_command(f".\\myvcs init")
    if "Initialized empty VCS repository" in out:
        messagebox.showinfo("Success", "Repository created successfully!")
        update_history()
    elif "Repository already exists" in out:
        messagebox.showwarning("Warning", "Repository already exists!")
    elif err:
        messagebox.showerror("Error", err)

def add_file():
    filename = file_entry.get()
    if not filename:
        messagebox.showwarning("Input Required", "Please enter a file name.")
        return
    repo_file_path = os.path.join(REPO_NAME, filename)
    if not os.path.exists(repo_file_path):
        # File does not exist in repo, create it
        create = messagebox.askyesno("File Not Found", f"'{filename}' does not exist in repo. Create it?")
        if create:
            with open(filename, "w") as f:
                f.write("")
            out, err = run_command(f".\\myvcs add {filename}")
            if "added to repository" in out:
                messagebox.showinfo("Success", f"File '{filename}' created and added to repository.")
                workspace.delete("1.0", "end")
                update_history()
            elif err:
                messagebox.showerror("Error", err)
        else:
            messagebox.showinfo("Cancelled", "File not added to repository.")
    else:
        # Save workspace content to file and add again
        content = workspace.get("1.0", "end-1c")
        with open(filename, "w") as f:
            f.write(content)
        out, err = run_command(f".\\myvcs add {filename}")
        if "added to repository" in out:
            messagebox.showinfo("Success", f"File '{filename}' updated in repository.")
            update_history()
        elif err:
            messagebox.showerror("Error", err)

def load_file_content():
    filename = file_entry.get()
    repo_file_path = os.path.join(REPO_NAME, filename)
    if os.path.exists(repo_file_path):
        with open(repo_file_path, "r") as f:
            content = f.read()
        workspace.delete("1.0", "end")
        workspace.insert("1.0", content)
    else:
        workspace.delete("1.0", "end")

def commit_file():
    filename = file_entry.get()
    if not filename:
        messagebox.showwarning("Input Required", "Please enter a file name.")
        return
    # Save workspace content to file before commit
    content = workspace.get("1.0", "end-1c")
    with open(filename, "w") as f:
        f.write(content)
    out, err = run_command(f".\\myvcs commit {filename}")
    if "committed" in out:
        messagebox.showinfo("Success", f"File '{filename}' committed.")
        update_history()
        update_timestamps(filename)
    elif err:
        messagebox.showerror("Error", err)

def update_history():
    # Show commit files in history
    history_box.configure(state="normal")
    history_box.delete("1.0", "end")
    commits_dir = os.path.join(REPO_NAME, "commits")
    if os.path.exists(commits_dir):
        for fname in sorted(os.listdir(commits_dir)):
            history_box.insert("end", fname + "\n")
    history_box.configure(state="disabled")

def update_timestamps(filename):
    # Update dropdown with timestamps for the selected file
    commits_dir = os.path.join(REPO_NAME, "commits")
    timestamps = []
    if os.path.exists(commits_dir):
        for fname in sorted(os.listdir(commits_dir)):
            if fname.startswith(filename + "."):
                ts = fname.split(".")[-1]
                timestamps.append(ts)
    timestamp_menu.configure(values=timestamps)
    if timestamps:
        timestamp_menu.set(timestamps[-1])
    else:
        timestamp_menu.set("")

def revert_file():
    filename = file_entry.get()
    timestamp = timestamp_menu.get()
    if not filename:
        messagebox.showwarning("Input Required", "Please enter a file name.")
        return
    if not timestamp:
        messagebox.showwarning("Input Required", "Please select a timestamp.")
        return
    out, err = run_command(f".\\myvcs revert {filename} {timestamp}")
    if "reverted" in out:
        messagebox.showinfo("Success", f"File '{filename}' reverted.")
        load_file_content()
        update_history()
    elif err:
        messagebox.showerror("Error", err)

app = ctk.CTk()
app.title("VCS")
app.geometry("750x450")

# Left panel (History) with Init button at the top
left_frame = ctk.CTkFrame(app, width=180)
left_frame.pack(side="left", fill="y", padx=10, pady=10)
init_btn = ctk.CTkButton(left_frame, text="Init Repository", command=init_repo)
init_btn.pack(pady=(10, 10))
ctk.CTkLabel(left_frame, text="VCS", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(10, 20))
ctk.CTkLabel(left_frame, text="History", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10)
history_box = ctk.CTkTextbox(left_frame, width=150, height=250, state="disabled")
history_box.pack(padx=10, pady=10)

# Right panel (Main actions)
right_frame = ctk.CTkFrame(app)
right_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

# File name + Add File button
file_row = ctk.CTkFrame(right_frame, fg_color="transparent")
file_row.pack(pady=(10, 5), anchor="nw")
file_entry = ctk.CTkEntry(file_row, placeholder_text="File name", width=200)
file_entry.pack(side="left", padx=(0, 10))
add_btn = ctk.CTkButton(file_row, text="Add File", command=add_file)
add_btn.pack(side="left")

# Timestamp dropdown + Revert button
ts_row = ctk.CTkFrame(right_frame, fg_color="transparent")
ts_row.pack(pady=(5, 5), anchor="nw")
timestamp_menu = ctk.CTkComboBox(ts_row, values=[], width=200)
timestamp_menu.pack(side="left", padx=(0, 10))
revert_btn = ctk.CTkButton(ts_row, text="Revert", command=revert_file)
revert_btn.pack(side="left")

# Workspace area for editing file content
workspace = ctk.CTkTextbox(right_frame, height=150, width=350)
workspace.pack(pady=10, fill="both", expand=True)

# Commit button at the bottom
commit_btn = ctk.CTkButton(right_frame, text="Commit", command=commit_file, width=350, height=40)
commit_btn.pack(pady=(10, 0))

# When file name changes, load content and update timestamps
def on_file_entry_change(*args):
    load_file_content()
    update_timestamps(file_entry.get())

file_entry.bind("<FocusOut>", lambda e: on_file_entry_change())
file_entry.bind("<Return>", lambda e: on_file_entry_change())

app.mainloop()
