import pandas as pd
import tkinter as tk
from tkinter import filedialog
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
    """Dynamically chooses how to load a file based on extension."""
    def __init__(self):
        self.loaders = {
            '.xlsx': ExcelLoader(),
            '.xls': ExcelLoader(),
            '.csv': CSVLoader()
        }

    def load_data(self, file_path: str) -> pd.DataFrame:
        ext = os.path.splitext(file_path)[1].lower()
        loader = self.loaders.get(ext)
        if not loader:
            raise ValueError(f"Unsupported file format: {ext}. Add a new loader to extend!")
        return loader.load(file_path)

# --- UI Function ---
def select_file_ui() -> str:
    """Opens a native UI window to select a file."""
    root = tk.Tk()
    root.withdraw() 
    root.attributes('-topmost', True) 
    
    file_path = filedialog.askopenfilename(
        title="Select Data File to Profile",
        filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv"), ("All files", "*.*")]
    )
    return file_path