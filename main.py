from data_loader import select_file_ui, DataLoaderEngine
from results import generate_sweetviz_report, generate_fuzzy_report

def main():
    # 1. Get the file path via UI
    file_path = select_file_ui()
    
    # If the user clicks "Cancel" on the popup window
    if not file_path:
        print("No file selected. Exiting.")
        return

    print(f"Selected File: {file_path}")

    # 2. Load the data 
    engine = DataLoaderEngine()
    try:
        df = engine.load_data(file_path)
        print(f"Data loaded successfully. Shape: {df.shape}")
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    # 3. Generate Results
    # This will create the HTML dashboard
    generate_sweetviz_report(df, output_filename="Sweetviz_Data_Profile.html")
    
    # This will create the CSV with fuzzy matching results
    generate_fuzzy_report(df, match_threshold=85, output_filename="Fuzzy_Matching_Report.csv")
    
    print("\nProfiling complete! Check your project folder for the output files.")

if __name__ == "__main__":
    main()