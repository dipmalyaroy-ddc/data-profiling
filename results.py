import pandas as pd
import sweetviz as sv
from fuzzywuzzy import process, fuzz
import matplotlib.pyplot as plt
import string
import plotly.express as px

def generate_sweetviz_report(df: pd.DataFrame, output_filename: str = "Sweetviz_Report.html"):
    print("Generating Sweetviz report (Global Dataset)...")
    report = sv.analyze(df)
    report.show_html(output_filename)
    print(f"Sweetviz report saved as '{output_filename}'")

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
            print(f"Invalid alpha filter format '{alpha_filter}'. Proceeding without filter.")
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
        
        # STEP 1: Bind Row, Exact String, and Traceback as a 3-part Tuple
        for idx, val in series.items():
            val_str = str(val).strip()
            if not val_str:
                continue
                
            if valid_letters and val_str[0].upper() not in valid_letters:
                continue

            if val_str not in exact_groups:
                exact_groups[val_str] = {'instances': []}
            
            row_num = idx + 2
            tb_val = str(df.loc[idx, traceback_col]) if traceback_col and traceback_col in df.columns else None
            
            # Store the strict 1-to-1-to-1 pairing
            exact_groups[val_str]['instances'].append((row_num, val_str, tb_val))
            
        unique_items = list(exact_groups.keys())
        before_count = len(unique_items) 
        if before_count == 0:
            continue
        
        # STEP 2: Apply Fuzzy Matching
        canonical_groups = {}
        for item in unique_items:
            data = exact_groups[item]
            
            if not canonical_groups:
                canonical_groups[item] = {'instances': data['instances']}
                continue

            best_match, score = process.extractOne(item, list(canonical_groups.keys()), scorer=fuzz.token_sort_ratio)

            if score >= match_threshold:
                # Merge the tuple lists together
                canonical_groups[best_match]['instances'].extend(data['instances'])
            else:
                canonical_groups[item] = {'instances': data['instances']}
        
        after_count = len(canonical_groups)
        histogram_data.append({'Column': col, 'Before': before_count, 'After': after_count})
        
        # STEP 3: Format the report (Ensuring 1-to-1-to-1 ordered mapping)
        for canonical, c_data in canonical_groups.items():
            # Sort instances strictly by Excel Row Number
            sorted_instances = sorted(c_data['instances'], key=lambda x: x[0])
            
            # Extract perfectly ordered lists
            ordered_rows = [str(inst[0]) for inst in sorted_instances]
            ordered_variations = [str(inst[1]) for inst in sorted_instances]
            ordered_tracebacks = [str(inst[2]) for inst in sorted_instances]
            
            report_row = {
                "Column Name": col,
                "Canonical Name": canonical,
                "Total Count": len(sorted_instances),
                # We use " | " instead of commas for variations just in case the brand names contain commas themselves
                "Variations Found": " | ".join(ordered_variations),
                "Excel Row Numbers": ", ".join(ordered_rows)
            }
            if traceback_col:
                report_row[f"Traceback ({traceback_col})"] = ", ".join(ordered_tracebacks)
            
            all_reports.append(report_row)

    # STEP 4: Export Data and Visualizations
    if all_reports:
        report_df = pd.DataFrame(all_reports).sort_values(by=["Column Name", "Total Count"], ascending=[True, False])
        report_df.to_csv(output_filename, index=False)
        print(f"Fuzzy matching report saved as '{output_filename}'")
        
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
            print(f"Before/After Histogram saved as '{plot_filename}'")

        print("\nGenerating interactive distribution charts...")
        for col_name in report_df['Column Name'].unique():
            col_data = report_df[report_df['Column Name'] == col_name].copy()
            dynamic_height = max(600, len(col_data) * 25)
            
            # Note: Hover data now shows the ordered variations string!
            fig = px.bar(
                col_data,
                x='Total Count',
                y='Canonical Name',
                orientation='h',
                title=f"Distribution of Fuzzy Matched Entities: {col_name}",
                hover_data=['Variations Found'],
                color='Total Count',
                color_continuous_scale=px.colors.sequential.Blues
            )
            
            fig.update_layout(
                height=dynamic_height,
                yaxis={'categoryorder': 'total ascending'},
                margin=dict(l=200)
            )
            
            safe_filename = "".join([c for c in col_name if c.isalnum() or c in (' ', '_')]).replace(' ', '_')
            html_out = f"Dist_{safe_filename}.html"
            
            fig.write_html(html_out)
            print(f"  Saved scrollable chart: '{html_out}'")

    else:
        print("No valid text data found matching your criteria.")