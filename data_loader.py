import pandas as pd
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
from abc import ABC, abstractmethod

# --- OCP File Loaders ---
class FileLoader(ABC):
    @abstractmethod
    def load(self, file_path: str) -> pd.DataFrame:
        pass

class ExcelLoader(FileLoader):
    def load(self, file_path: str) -> pd.DataFrame:
        return pd.read_excel(file_path)

class CSVLoader(FileLoader):
    def load(self, file_path: str) -> pd.DataFrame:
        return pd.read_csv(file_path)

class DataLoaderEngine:
    def __init__(self):
        self.loaders = {'.xlsx': ExcelLoader(), '.xls': ExcelLoader(), '.csv': CSVLoader()}

    def load_data(self, file_path: str) -> pd.DataFrame:
        ext = os.path.splitext(file_path)[1].lower()
        loader = self.loaders.get(ext)
        if not loader:
            raise ValueError(f"Unsupported file format: {ext}")
        return loader.load(file_path)

# --- UI Functions ---
def select_file_ui() -> str:
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    file_path = filedialog.askopenfilename(
        title="Select Data File to Profile",
        filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv"), ("All files", "*.*")]
    )

    root.destroy()
    return file_path

def get_user_configuration(columns: list) -> dict:
    """Opens a UI to select target columns, traceback column, and alpha filter."""
    config = {}

    root = tk.Tk()
    root.title("Data Profiler Configuration")
    root.geometry("480x550")

    root.attributes('-topmost', True)
    root.lift()
    root.focus_force()

    # 1. Profile All vs Custom
    tk.Label(root, text="1. Column Selection:", font=('Arial', 10, 'bold')).pack(anchor="w", padx=10, pady=(10,0))

    selection_var = tk.StringVar(value="All")

    def toggle_listbox():
        if selection_var.get() == "Custom":
            listbox.config(fg="black")
        else:
            listbox.config(fg="gray")
            listbox.selection_clear(0, tk.END)

    tk.Radiobutton(root, text="Profile All Text Columns", variable=selection_var, value="All", command=toggle_listbox).pack(anchor="w", padx=20)
    tk.Radiobutton(root, text="Customize Selection (Click to enable list below)", variable=selection_var, value="Custom", command=toggle_listbox).pack(anchor="w", padx=20)

    # Frame for Listbox and Scrollbar
    list_frame = tk.Frame(root)
    list_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=5)

    scrollbar = tk.Scrollbar(list_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    listbox = tk.Listbox(
        list_frame,
        selectmode=tk.MULTIPLE,
        height=8,
        bg="white",
        fg="gray",
        selectbackground="#4CAF50",
        selectforeground="white",
        exportselection=False,
        yscrollcommand=scrollbar.set
    )
    for col in columns:
        listbox.insert(tk.END, col)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=listbox.yview)

    # 2. Traceback Column
    tk.Label(root, text="2. Traceback Column (Optional):", font=('Arial', 10, 'bold')).pack(anchor="w", padx=10, pady=(15,0))
    traceback_var = tk.StringVar()
    traceback_dropdown = ttk.Combobox(root, textvariable=traceback_var, values=["None"] + columns, state="readonly")
    traceback_dropdown.current(0)
    traceback_dropdown.pack(fill=tk.X, padx=30, pady=5)

    # 3. Alphabet Filter
    tk.Label(root, text="3. Alphabet Filter (Optional):", font=('Arial', 10, 'bold')).pack(anchor="w", padx=10, pady=(15,0))
    tk.Label(root, text="e.g., 'A' for single letter, or 'A-F' for range. Leave blank for all.", font=('Arial', 8)).pack(anchor="w", padx=30)
    alpha_var = tk.StringVar()
    tk.Entry(root, textvariable=alpha_var, bg="white", fg="black").pack(fill=tk.X, padx=30, pady=5)

    def on_submit():
        if selection_var.get() == "Custom":
            selected_indices = listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("Warning", "Please select at least one column from the list.")
                root.attributes('-topmost', True)
                return
            config['selected_columns'] = [listbox.get(i) for i in selected_indices]
        else:
            config['selected_columns'] = "All"

        config['traceback'] = traceback_var.get() if traceback_var.get() != "None" else None
        config['alpha_filter'] = alpha_var.get().strip().upper()
        root.quit()
        root.destroy()

    tk.Button(root, text="Run Profiler", command=on_submit, bg="#4CAF50", fg="white", font=('Arial', 10, 'bold')).pack(pady=20, fill=tk.X, padx=50)

    root.mainloop()
    return config