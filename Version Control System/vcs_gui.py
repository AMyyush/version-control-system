import customtkinter as ctk
from tkinter import messagebox
from tkinter import Listbox
import os
import subprocess
import speech_recognition as sr
import difflib
import tkinter as tk
from PIL import Image, ImageTk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("VCS")
app.geometry("1100x500")

# --- Icons ---
icon_commit = ImageTk.PhotoImage(Image.open("icons8-page-64.png").resize((20, 20)))
icon_voice = ImageTk.PhotoImage(Image.open("icons8-voice-50.png").resize((20, 20)))
icon_diff = ImageTk.PhotoImage(Image.open("icons8-change.gif").resize((20, 20)))

current_repo = ctk.StringVar(value="MyRepo")

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return "", str(e)

def get_repos():
    return [f for f in os.listdir() if os.path.isdir(f) and f != "__pycache__"]

def update_file_list():
    file_listbox.delete(0, "end")
    repo_path = current_repo.get()
    if os.path.exists(repo_path):
        for fname in sorted(os.listdir(repo_path)):
            if fname != "commits" and os.path.isfile(os.path.join(repo_path, fname)):
                file_listbox.insert("end", fname)

def update_repo_list():
    repo_listbox.delete(0, "end")
    for repo in get_repos():
        repo_listbox.insert("end", repo)
    repos = repo_listbox.get(0, "end")
    for idx, repo in enumerate(repos):
        if repo == current_repo.get():
            repo_listbox.selection_clear(0, "end")
            repo_listbox.selection_set(idx)
            repo_listbox.see(idx)
            break

def update_history():
    history_box.configure(state="normal")
    history_box.delete("1.0", "end")
    commits_dir = os.path.join(current_repo.get(), "commits")
    if os.path.exists(commits_dir):
        for fname in sorted(os.listdir(commits_dir)):
            history_box.insert("end", fname + "\n")
    history_box.configure(state="disabled")

def update_timestamps(filename):
    commits_dir = os.path.join(current_repo.get(), "commits")
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

def update_all_panels():
    update_history()
    update_file_list()
    update_repo_list()
    repo_label.configure(text=f"Repository: {current_repo.get()}")

def update_suggestion():
    repo_exists = os.path.exists(current_repo.get())
    filename = file_entry.get()
    repo_file_path = os.path.join(current_repo.get(), filename)
    commits_dir = os.path.join(current_repo.get(), "commits")
    suggestion = ""
    if not repo_exists:
        suggestion = "Suggestion: Create or open a repository."
    elif not filename:
        suggestion = "Suggestion: Enter a file name and click 'Add File'."
    elif not os.path.exists(repo_file_path):
        suggestion = "Suggestion: Click 'Add File' to create and add this file."
    elif os.path.exists(repo_file_path) and not os.path.exists(commits_dir):
        suggestion = "Suggestion: Click 'Commit' to save a version."
    elif os.path.exists(commits_dir):
        suggestion = "Suggestion: You can 'Commit' changes or 'Revert' to a previous version."
    suggestion_label.configure(text=suggestion)

def select_file_in_panel(filename):
    files = file_listbox.get(0, "end")
    for idx, fname in enumerate(files):
        if fname == filename:
            file_listbox.selection_clear(0, "end")
            file_listbox.selection_set(idx)
            file_listbox.see(idx)
            break

def on_file_select(event):
    selection = file_listbox.curselection()
    if selection:
        line = file_listbox.get(selection[0])
        file_entry.delete(0, "end")
        file_entry.insert(0, line)
        load_file_content()
        update_timestamps(line)
        update_suggestion()

def on_repo_select(event):
    selection = repo_listbox.curselection()
    if selection:
        repo = repo_listbox.get(selection[0])
        current_repo.set(repo)
        update_all_panels()
        update_suggestion()

def on_file_entry_change(*args):
    load_file_content()
    update_timestamps(file_entry.get())
    select_file_in_panel(file_entry.get())

def open_or_create_repo(repo):
    repo = repo.strip()
    if not repo:
        messagebox.showwarning("Input Required", "Please enter a repository name.")
        return
    if os.path.exists(repo):
        current_repo.set(repo)
        update_all_panels()
        update_suggestion()
    else:
        out, err = run_command(f".\\myvcs init {repo}")
        if "Initialized empty VCS repository" in out or not err:
            messagebox.showinfo("Success", f"Repository '{repo}' created successfully!")
            current_repo.set(repo)
            update_all_panels()
            update_suggestion()
        else:
            messagebox.showerror("Error", err or "Failed to create repository.")

def add_file():
    filename = file_entry.get()
    if not filename:
        messagebox.showwarning("Input Required", "Please enter a file name.")
        return
    repo_file_path = os.path.join(current_repo.get(), filename)
    if not os.path.exists(repo_file_path):
        create = messagebox.askyesno("File Not Found", f"'{filename}' does not exist in repo. Create it?")
        if create:
            with open(filename, "w") as f:
                f.write("")
            out, err = run_command(f".\\myvcs add {current_repo.get()} {filename}")
            if "added to repository" in out:
                messagebox.showinfo("Success", f"File '{filename}' created and added to repository.")
                workspace.delete("1.0", "end")
                update_all_panels()
            elif err:
                messagebox.showerror("Error", err)
        else:
            messagebox.showinfo("Cancelled", "File not added to repository.")
    else:
        content = workspace.get("1.0", "end-1c")
        with open(filename, "w") as f:
            f.write(content)
        out, err = run_command(f".\\myvcs add {current_repo.get()} {filename}")
        if "added to repository" in out:
            messagebox.showinfo("Success", f"File '{filename}' updated in repository.")
            update_all_panels()
        elif err:
            messagebox.showerror("Error", err)
    update_suggestion()

def update_content():
    filename = file_entry.get()
    if not filename:
        messagebox.showwarning("Input Required", "Please enter a file name.")
        return
    repo_file_path = os.path.join(current_repo.get(), filename)
    if not os.path.exists(repo_file_path):
        messagebox.showwarning("File Not Found", f"'{filename}' does not exist in the repository.")
        return
    content = workspace.get("1.0", "end-1c")
    with open(filename, "w") as f:
        f.write(content)
    out, err = run_command(f".\\myvcs add {current_repo.get()} {filename}")
    if "added to repository" in out:
        messagebox.showinfo("Success", f"Content of '{filename}' updated in repository.")
        update_all_panels()
    elif err:
        messagebox.showerror("Error", err)
    update_suggestion()

def load_file_content():
    filename = file_entry.get()
    repo_file_path = os.path.join(current_repo.get(), filename)
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
    content = workspace.get("1.0", "end-1c")
    with open(filename, "w") as f:
        f.write(content)
    out, err = run_command(f".\\myvcs commit {current_repo.get()} {filename}")
    if "committed" in out:
        messagebox.showinfo("Success", f"File '{filename}' committed.")
        update_all_panels()
        update_timestamps(filename)
    elif err:
        messagebox.showerror("Error", err)
    update_suggestion()

def revert_file():
    filename = file_entry.get()
    timestamp = timestamp_menu.get()
    if not filename:
        messagebox.showwarning("Input Required", "Please enter a file name.")
        return
    if not timestamp:
        messagebox.showwarning("Input Required", "Please select a timestamp.")
        return
    out, err = run_command(f".\\myvcs revert {current_repo.get()} {filename} {timestamp}")
    if "reverted" in out:
        messagebox.showinfo("Success", f"File '{filename}' reverted.")
        load_file_content()
        update_all_panels()
    elif err:
        messagebox.showerror("Error", err)
    update_suggestion()

def show_diff():
    filename = file_entry.get()
    if not filename:
        messagebox.showwarning("Input Required", "Please enter a file name.")
        return

    current_content = workspace.get("1.0", "end-1c").splitlines()
    commits_dir = os.path.join(current_repo.get(), "commits")
    committed_content = []
    if os.path.exists(commits_dir):
        versions = [f for f in os.listdir(commits_dir) if f.startswith(filename + ".")]
        if versions:
            latest_version = sorted(versions)[-1]
            with open(os.path.join(commits_dir, latest_version), "r") as f:
                committed_content = f.read().splitlines()
        else:
            messagebox.showinfo("No Commit", "No committed version found for this file.")
            return
    else:
        messagebox.showinfo("No Commit", "No committed version found for this file.")
        return

    diff = difflib.ndiff(committed_content, current_content)
    diff_lines = []
    for line in diff:
        if line.startswith('- '):
            diff_lines.append(f"Removed: {line[2:]}")
        elif line.startswith('+ '):
            diff_lines.append(f"Added: {line[2:]}")
    if not diff_lines:
        diff_lines = ["No differences found."]

    diff_text = "\n".join(diff_lines)

    diff_window = ctk.CTkToplevel(app)
    diff_window.title("Diff: Committed vs Current")
    diff_window.geometry("700x400")
    diff_box = ctk.CTkTextbox(diff_window, width=680, height=380)
    diff_box.pack(padx=10, pady=10, fill="both", expand=True)
    diff_box.insert("1.0", diff_text)
    diff_box.configure(state="disabled")

def voice_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        messagebox.showinfo("Voice Command", "Listening... Please speak your command.")
        audio = recognizer.listen(source)
    try:
        command = recognizer.recognize_google(audio).lower()
        messagebox.showinfo("Recognized Command", f"You said: {command}")
        if "init" in command:
            open_or_create_repo(repo_name_entry.get())
        elif "add" in command:
            add_file()
        elif "update" in command:
            update_content()
        elif "commit" in command:
            commit_file()
        elif "revert" in command:
            revert_file()
        else:
            messagebox.showwarning("Unknown Command", "Command not recognized. Try saying: init, add, update, commit, or revert.")
    except Exception as e:
        messagebox.showerror("Error", f"Could not recognize your voice. {e}")

# --- UI Layout ---

# Repo name entry and open/create button
repo_name_entry = ctk.CTkEntry(app, placeholder_text="Repository name", width=200)
repo_name_entry.pack(side="top", padx=10, pady=(10,0))
repo_action_btn = ctk.CTkButton(app, text="Open/Create Repository", command=lambda: open_or_create_repo(repo_name_entry.get()))
repo_action_btn.pack(side="top", padx=10, pady=(15,10))

# Left panel (History)
left_frame = ctk.CTkFrame(app, width=180)
left_frame.pack(side="left", fill="y", padx=10, pady=10)
ctk.CTkLabel(left_frame, text="VCS", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(10, 20))
ctk.CTkLabel(left_frame, text="History", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10)
history_box = ctk.CTkTextbox(left_frame, width=150, height=250, state="disabled")
history_box.pack(padx=10, pady=10)

# Rightmost file panel (vertical)
file_panel = ctk.CTkFrame(app, width=200)
file_panel.pack(side="right", fill="y", padx=10, pady=10)

ctk.CTkLabel(file_panel, text="Repositories", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
repo_listbox = Listbox(
    file_panel,
    height=5,
    width=25,
    bg="#23272f",
    fg="white",
    font=("Arial", 14, "bold"),
    selectbackground="#2563eb",
    selectforeground="white",
    borderwidth=2,
    relief="solid",
    highlightthickness=0
)
repo_listbox.pack(padx=10, pady=(0, 10), fill="x")
repo_listbox.bind("<<ListboxSelect>>", on_repo_select)

repo_label = ctk.CTkLabel(file_panel, text=f"Repository: {current_repo.get()}", font=ctk.CTkFont(size=14, weight="bold"))
repo_label.pack(pady=(0, 10))

ctk.CTkLabel(file_panel, text="Files in Repo", font=ctk.CTkFont(size=16, weight="bold")).pack()
file_listbox = Listbox(
    file_panel,
    height=15,
    width=25,
    bg="#23272f",
    fg="white",
    font=("Arial", 16, "bold"),
    selectbackground="#2563eb",
    selectforeground="white",
    borderwidth=2,
    relief="solid",
    highlightthickness=0
)
file_listbox.pack(padx=10, pady=(0,10), fill="y", expand=True)
file_listbox.bind("<<ListboxSelect>>", on_file_select)

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
update_btn = ctk.CTkButton(file_row, text="Update Content", command=update_content)
update_btn.pack(side="left", padx=(10, 0))

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
commit_btn = ctk.CTkButton(right_frame, text="Commit", image=icon_commit, command=commit_file, width=350, height=40, compound="left")
commit_btn.pack(pady=(10, 0))

# Voice Command button
voice_btn = ctk.CTkButton(right_frame, text="Voice Command", image=icon_voice, command=voice_command, width=350, height=40, compound="left")
voice_btn.pack(pady=(10, 0))

# Show Diff button
diff_btn = ctk.CTkButton(right_frame, text="Show Diff", image=icon_diff, command=show_diff, width=350, height=40, compound="left")
diff_btn.pack(pady=(10, 0))

# Suggestion label
suggestion_label = ctk.CTkLabel(right_frame, text="", font=ctk.CTkFont(size=14, weight="bold"), text_color="#00BFFF")
suggestion_label.pack(pady=(0, 5), anchor="nw")

# Bind file entry changes
file_entry.bind("<FocusOut>", lambda e: (on_file_entry_change(), update_suggestion()))
file_entry.bind("<Return>", lambda e: (on_file_entry_change(), update_suggestion()))

# Initial panel update
update_all_panels()
update_suggestion()

app.mainloop()
