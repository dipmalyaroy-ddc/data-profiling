from data_loader import select_file_ui, DataLoaderEngine, get_user_configuration
from results import generate_sweetviz_report, generate_fuzzy_report

def main():
    # 1. UI File Selection
    file_path = select_file_ui()
    if not file_path:
        print("No file selected. Exiting.")
        return

    print(f"Loading: {file_path}")

    # 2. Load Data 
    engine = DataLoaderEngine()
    try:
        df = engine.load_data(file_path)
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    # 3. UI Configuration (Select Columns, Traceback, Alpha Filter)
    columns_list = df.columns.tolist()
    config = get_user_configuration(columns_list)
    
    if not config:
        print("Configuration cancelled. Exiting.")
        return

    # 4. Generate Reports
    generate_sweetviz_report(df)
    generate_fuzzy_report(df, config=config, match_threshold=85)
    
    print("\n🎉 Profiling complete! Check your project folder.")

if __name__ == "__main__":
    main()