import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

class VCSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini Version Control System")
        self.backend_exe = "myvcs.exe"  # Update if needed
        self.repo_name = ""

        self.repo_label = tk.Label(root, text="Repository Name:")
        self.repo_label.pack()
        self.repo_entry = tk.Entry(root)
        self.repo_entry.pack()

        self.init_button = tk.Button(root, text="Create Repository", command=self.init_repo)
        self.init_button.pack(pady=5)

        self.filename_label = tk.Label(root, text="File Name:")
        self.filename_label.pack()
        self.filename_entry = tk.Entry(root)
        self.filename_entry.pack()

        self.add_button = tk.Button(root, text="Add File", command=self.add_file)
        self.add_button.pack(pady=5)

        self.edit_area = scrolledtext.ScrolledText(root, width=60, height=15)
        self.edit_area.pack(pady=5)

        self.save_button = tk.Button(root, text="Save File", command=self.save_file)
        self.save_button.pack(pady=5)

        self.commit_button = tk.Button(root, text="Commit File", command=self.commit_file)
        self.commit_button.pack(pady=5)

        self.revert_button = tk.Button(root, text="Revert File", command=self.revert_file)
        self.revert_button.pack(pady=5)

    def init_repo(self):
        self.repo_name = self.repo_entry.get()
        if not self.repo_name:
            messagebox.showerror("Error", "Please enter a repository name.")
            return
        result = subprocess.run([self.backend_exe, "init"], cwd=os.getcwd())
        messagebox.showinfo("Info", f"Repository '{self.repo_name}' initialized.")

    def add_file(self):
        filename = self.filename_entry.get()
        if not filename:
            messagebox.showerror("Error", "Enter filename to add.")
            return

        filepath = os.path.join(os.getcwd(), filename)
        if not os.path.exists(filepath):
            if messagebox.askyesno("File Missing", f"'{filename}' doesn't exist. Create it?"):
                with open(filepath, "w") as f:
                    f.write("")
                messagebox.showinfo("Created", f"File '{filename}' created.")

        subprocess.run([self.backend_exe, "add", filename])
        with open(filepath, "r") as f:
            self.edit_area.delete("1.0", tk.END)
            self.edit_area.insert(tk.END, f.read())

    def save_file(self):
        filename = self.filename_entry.get()
        if not filename:
            return
        filepath = os.path.join(os.getcwd(), filename)
        with open(filepath, "w") as f:
            f.write(self.edit_area.get("1.0", tk.END))
        messagebox.showinfo("Saved", f"Changes saved to '{filename}'.")

    def commit_file(self):
        filename = self.filename_entry.get()
        subprocess.run([self.backend_exe, "commit", filename])
        messagebox.showinfo("Committed", f"'{filename}' committed.")

    def revert_file(self):
        filename = self.filename_entry.get()
        subprocess.run([self.backend_exe, "revert", filename])
        with open(filename, "r") as f:
            self.edit_area.delete("1.0", tk.END)
            self.edit_area.insert(tk.END, f.read())
        messagebox.showinfo("Reverted", f"'{filename}' reverted.")

if __name__ == "__main__":
    root = tk.Tk()
    app = VCSApp(root)
    root.mainloop()