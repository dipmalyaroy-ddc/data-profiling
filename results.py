import pandas as pd
import sweetviz as sv
from fuzzywuzzy import process, fuzz
import matplotlib.pyplot as plt

def generate_sweetviz_report(df: pd.DataFrame, output_filename: str = "Sweetviz_Report.html"):
    """Generates and opens a Sweetviz HTML visualization."""
    print("Generating Sweetviz report...")
    report = sv.analyze(df)
    report.show_html(output_filename)
    print(f"Sweetviz report saved as '{output_filename}'")

def generate_fuzzy_report(df: pd.DataFrame, match_threshold: int = 85, output_filename: str = "Fuzzy_Match_Results.csv", plot_filename: str = "Fuzzy_Impact_Histogram.png"):
    """Performs fuzzy matching, tracks Excel row numbers, and plots a Before/After Histogram."""
    print("\nRunning Fuzzy Match Distinct Count Profiler...")
    
    text_cols = df.select_dtypes(include=['object', 'string']).columns
    all_reports = []
    histogram_data = [] # Stores before/after counts for the chart

    for col in text_cols:
        col_lower = col.lower()
        # Skip ID, Code, or Timestamp columns
        if any(x in col_lower for x in ['id', 'code', 'timestamp', 'sequence']):
            print(f"  -> Skipping ID/Code Column: '{col}'")
            continue
            
        print(f"  -> Profiling Text Column: '{col}'")
        
        # Drop empty values
        series = df[col].dropna()
        if series.empty:
            continue
            
        # STEP 1: Get exact matches and their original Excel row numbers
        # Pandas index starts at 0. In Excel, row 1 is headers, so data starts at row 2. 
        # Therefore, Excel Row = Pandas Index + 2
        exact_groups = {}
        for idx, val in series.items():
            val_str = str(val).strip()
            if val_str not in exact_groups:
                exact_groups[val_str] = []
            exact_groups[val_str].append(idx + 2)
            
        unique_items = list(exact_groups.keys())
        before_count = len(unique_items) # Distinct count BEFORE fuzzy matching
        
        # STEP 2: Apply Fuzzy Matching
        canonical_groups = {}
        
        for item in unique_items:
            rows = exact_groups[item]
            
            if not canonical_groups:
                canonical_groups[item] = {'variations': {item}, 'rows': rows}
                continue

            # Find the best match among existing canonical names
            best_match, score = process.extractOne(
                item, list(canonical_groups.keys()), scorer=fuzz.token_sort_ratio
            )

            if score >= match_threshold:
                # Group them together, combine their row numbers and variations
                canonical_groups[best_match]['variations'].add(item)
                canonical_groups[best_match]['rows'].extend(rows)
            else:
                # Create a new canonical group
                canonical_groups[item] = {'variations': {item}, 'rows': rows}
        
        after_count = len(canonical_groups) # Distinct count AFTER fuzzy matching
        
        # Save counts for our chart
        if before_count > 0:
            histogram_data.append({'Column': col, 'Before': before_count, 'After': after_count})
        
        # STEP 3: Format the detailed table
        for canonical, data in canonical_groups.items():
            all_reports.append({
                "Column Name": col,
                "Canonical Name": canonical,
                "Total Count": len(data['rows']),
                "Variations Found": " | ".join(data['variations']),
                "Excel Row Numbers": ", ".join(map(str, sorted(data['rows'])))
            })

    # STEP 4: Save outputs
    if all_reports:
        # Save the CSV Table
        report_df = pd.DataFrame(all_reports).sort_values(by=["Column Name", "Total Count"], ascending=[True, False])
        report_df.to_csv(output_filename, index=False)
        print(f"\n✅ Fuzzy matching report saved as '{output_filename}'")
        
        # Generate and Save the Histogram Plot
        if histogram_data:
            plot_df = pd.DataFrame(histogram_data)
            
            # Setup the bar chart
            fig, ax = plt.subplots(figsize=(10, 6))
            x = range(len(plot_df))
            width = 0.35
            
            # Plot the Before and After bars side-by-side
            ax.bar([i - width/2 for i in x], plot_df['Before'], width, label='Before Fuzzy Match (Strict)', color='#3498db')
            ax.bar([i + width/2 for i in x], plot_df['After'], width, label='After Fuzzy Match (Grouped)', color='#e74c3c')
            
            # Formatting labels and title
            ax.set_ylabel('Distinct Items Count', fontsize=12)
            ax.set_title('Impact of Fuzzy Matching on Distinct Counts', fontsize=14, pad=15)
            ax.set_xticks(x)
            ax.set_xticklabels(plot_df['Column'], rotation=45, ha="right", fontsize=10)
            ax.legend()
            
            # Save the image
            plt.tight_layout()
            plt.savefig(plot_filename)
            print(f"✅ Before/After Histogram saved as '{plot_filename}'")
            
    else:
        print("No valid text data found to profile.")