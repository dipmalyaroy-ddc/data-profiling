import pandas as pd
import sweetviz as sv
from fuzzywuzzy import process, fuzz
import matplotlib.pyplot as plt
import string
import plotly.express as px  # <-- NEW: Interactive charting engine

def generate_sweetviz_report(df: pd.DataFrame, output_filename: str = "Sweetviz_Report.html"):
    print("Generating Sweetviz report (Global Dataset)...")
    report = sv.analyze(df)
    report.show_html(output_filename)
    print(f"✅ Sweetviz report saved as '{output_filename}'")

def get_valid_letters(alpha_filter: str):
    """Parses 'A' or 'A-F' into a list of valid starting letters."""
    if not alpha_filter:
        return None
    if '-' in alpha_filter:
        try:
            start, end = alpha_filter.split('-')
            start_idx = string.ascii_uppercase.index(start.strip())
            end_idx = string.ascii_uppercase.index(end.strip())
            return list(string.ascii_uppercase[start_idx:end_idx+1])
        except ValueError:
            print(f"⚠️ Invalid alpha filter format '{alpha_filter}'. Proceeding without filter.")
            return None
    return [alpha_filter.strip()]

def generate_fuzzy_report(df: pd.DataFrame, config: dict, match_threshold: int = 85, output_filename: str = "Fuzzy_Match_Results.csv", plot_filename: str = "Fuzzy_Impact_Histogram.png"):
    print("\n--- Running Custom Fuzzy Match Profiler ---")
    
    if config['selected_columns'] == "All":
        cols_to_profile = df.select_dtypes(include=['object', 'string']).columns.tolist()
    else:
        cols_to_profile = config['selected_columns']

    traceback_col = config.get('traceback')
    valid_letters = get_valid_letters(config.get('alpha_filter'))
    
    all_reports = []
    histogram_data = []

    for col in cols_to_profile:
        print(f"  -> Profiling: '{col}'")
        series = df[col].dropna()
        if series.empty:
            continue
            
        exact_groups = {}
        
        # STEP 1: Get exact matches, filter by alphabet, and log Row/Traceback
        for idx, val in series.items():
            val_str = str(val).strip()
            if not val_str:
                continue
                
            if valid_letters and val_str[0].upper() not in valid_letters:
                continue

            if val_str not in exact_groups:
                exact_groups[val_str] = {'rows': [], 'tracebacks': set()}
            
            exact_groups[val_str]['rows'].append(idx + 2)
            if traceback_col and traceback_col in df.columns:
                exact_groups[val_str]['tracebacks'].add(str(df.loc[idx, traceback_col]))
            
        unique_items = list(exact_groups.keys())
        before_count = len(unique_items) 
        if before_count == 0:
            continue
        
        # STEP 2: Apply Fuzzy Matching
        canonical_groups = {}
        for item in unique_items:
            data = exact_groups[item]
            
            if not canonical_groups:
                canonical_groups[item] = {'variations': {item}, 'rows': data['rows'], 'tracebacks': data['tracebacks']}
                continue

            best_match, score = process.extractOne(item, list(canonical_groups.keys()), scorer=fuzz.token_sort_ratio)

            if score >= match_threshold:
                canonical_groups[best_match]['variations'].add(item)
                canonical_groups[best_match]['rows'].extend(data['rows'])
                canonical_groups[best_match]['tracebacks'].update(data['tracebacks'])
            else:
                canonical_groups[item] = {'variations': {item}, 'rows': data['rows'], 'tracebacks': data['tracebacks']}
        
        after_count = len(canonical_groups)
        histogram_data.append({'Column': col, 'Before': before_count, 'After': after_count})
        
        # STEP 3: Format the report
        for canonical, c_data in canonical_groups.items():
            report_row = {
                "Column Name": col,
                "Canonical Name": canonical,
                "Total Count": len(c_data['rows']),
                "Variations Found": " | ".join(c_data['variations']),
                "Excel Row Numbers": ", ".join(map(str, sorted(c_data['rows'])))
            }
            if traceback_col:
                report_row[f"Traceback ({traceback_col})"] = ", ".join(sorted(c_data['tracebacks']))
            all_reports.append(report_row)

    # STEP 4: Export Data and Visualizations
    if all_reports:
        # Save the master CSV
        report_df = pd.DataFrame(all_reports).sort_values(by=["Column Name", "Total Count"], ascending=[True, False])
        report_df.to_csv(output_filename, index=False)
        print(f"✅ Fuzzy matching report saved as '{output_filename}'")
        
        # Save the Before/After impact summary PNG
        if histogram_data:
            plot_df = pd.DataFrame(histogram_data)
            fig, ax = plt.subplots(figsize=(10, 6))
            x = range(len(plot_df))
            width = 0.35
            
            ax.bar([i - width/2 for i in x], plot_df['Before'], width, label='Before (Strict)', color='#3498db')
            ax.bar([i + width/2 for i in x], plot_df['After'], width, label='After (Fuzzy)', color='#e74c3c')
            
            ax.set_ylabel('Distinct Items Count', fontsize=12)
            ax.set_title(f"Impact of Fuzzy Matching {'(Filtered)' if valid_letters else ''}", fontsize=14, pad=15)
            ax.set_xticks(x)
            ax.set_xticklabels(plot_df['Column'], rotation=45, ha="right", fontsize=10)
            ax.legend()
            
            plt.tight_layout()
            plt.savefig(plot_filename)
            print(f"✅ Before/After Histogram saved as '{plot_filename}'")

        # --- NEW: GENERATE INTERACTIVE DISTRIBUTION CHARTS PER COLUMN ---
        print("\nGenerating interactive distribution charts...")
        for col_name in report_df['Column Name'].unique():
            col_data = report_df[report_df['Column Name'] == col_name].copy()
            
            # Dynamically calculate the height of the webpage so 68K rows don't get squished
            # We allocate ~25 pixels of vertical space per bar
            dynamic_height = max(600, len(col_data) * 25)
            
            fig = px.bar(
                col_data,
                x='Total Count',
                y='Canonical Name',
                orientation='h', # Horizontal makes text easy to read
                title=f"Distribution of Fuzzy Matched Entities: {col_name}",
                hover_data=['Variations Found'], # Tooltip shows what got merged!
                color='Total Count', # Optional: adds a nice heat map color scale based on volume
                color_continuous_scale=px.colors.sequential.Blues
            )
            
            # Sort bars with largest counts at the top
            fig.update_layout(
                height=dynamic_height,
                yaxis={'categoryorder': 'total ascending'},
                margin=dict(l=200) # Give extra room for long brand names
            )
            
            # Strip illegal characters from the column name to create a safe file name
            safe_filename = "".join([c for c in col_name if c.isalnum() or c in (' ', '_')]).replace(' ', '_')
            html_out = f"Dist_{safe_filename}.html"
            
            fig.write_html(html_out)
            print(f"  📊 Saved scrollable chart: '{html_out}'")

    else:
        print("No valid text data found matching your criteria.")