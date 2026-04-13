import pandas as pd
import sweetviz as sv
from fuzzywuzzy import process, fuzz

def generate_sweetviz_report(df: pd.DataFrame, output_filename: str = "Sweetviz_Report.html"):
    """Generates and opens a Sweetviz HTML visualization."""
    print("Generating Sweetviz report...")
    report = sv.analyze(df)
    report.show_html(output_filename)
    print(f"Sweetviz report saved as '{output_filename}'")

def generate_fuzzy_report(df: pd.DataFrame, match_threshold: int = 70, output_filename: str = "Fuzzy_Match_Results.csv"):
    """Performs fuzzy matching on text columns and saves the detailed report to a CSV."""
    print("\nRunning Fuzzy Match Distinct Count Profiler...")
    
    # Dynamically find text columns
    text_cols = df.select_dtypes(include=['object', 'string']).columns
    all_reports = []

    for col in text_cols:
        print(f"  -> Profiling Column: '{col}'")
        items = df[col].dropna().astype(str).tolist()
        unique_items = list(set(items))

        if not unique_items:
            continue

        canonical_map = {}
        canonical_counts = {}
        variations = {}

        for item in unique_items:
            if not canonical_counts:
                canonical_map[item] = item
                canonical_counts[item] = items.count(item)
                variations[item] = {item}
                continue

            # FuzzyWuzzy matching
            best_match, score = process.extractOne(
                item, list(canonical_counts.keys()), scorer=fuzz.token_sort_ratio
            )

            if score >= match_threshold:
                canonical_map[item] = best_match
                canonical_counts[best_match] += items.count(item)
                variations[best_match].add(item)
            else:
                canonical_map[item] = item
                canonical_counts[item] = items.count(item)
                variations[item] = {item}

        # Format results for this column
        for canonical, count in canonical_counts.items():
            all_reports.append({
                "Column Name": col,
                "Canonical Name": canonical,
                "Total Count": count,
                "Variations Found": " | ".join(variations[canonical])
            })

    # Save to file
    if all_reports:
        report_df = pd.DataFrame(all_reports).sort_values(by=["Column Name", "Total Count"], ascending=[True, False])
        report_df.to_csv(output_filename, index=False)
        print(f"Fuzzy matching report saved as '{output_filename}'")
    else:
        print("No text data found to profile.")