# Enterprise Data Profiling & Entity Resolution Engine

A robust, modular Python utility designed for automated data profiling and intelligent entity resolution. This engine dynamically ingests datasets, generates comprehensive Exploratory Data Analysis (EDA) dashboards, and utilizes probabilistic matching to clean, cluster, and deduplicate textual data while maintaining strict data lineage.

---

## Detailed Installation Guide

This project requires Python 3.7 or higher. To ensure a clean deployment, it is recommended to run this tool within a dedicated Python environment.

### Step 1: Environment Setup
Ensure you have downloaded the project repository to your local machine. Open your computer's Terminal (Mac/Linux) or Command Prompt (Windows). 

Navigate to the project directory using the `cd` command. For example:
`cd path/to/your/data_profiler_project`

### Step 2: Install Dependencies
The project utilizes a `requirements.txt` file, which acts as a manifest for all the underlying data science libraries (including Pandas, Sweetviz, and FuzzyWuzzy). 

To install all required packages simultaneously, run the following command in your terminal:
`pip install -r requirements.txt`

*Note: Wait for the terminal to finish downloading and installing all packages before proceeding.*

---

## Execution Instructions

The application is built with the Open/Closed Principle (OCP), allowing for seamless execution without requiring users to modify the underlying source code. 

To run the engine, execute the following command in your terminal while inside the project directory:
`python main.py`

**What to expect during execution:**
1. **File Selection:** A native operating system window will immediately open. Use this window to locate and select your target data file (`.csv`, `.xls`, or `.xlsx`).
2. **Background Processing:** Once selected, the terminal will output status updates. The engine will automatically parse the schema, isolate textual dimensions, and bypass unique identifiers (such as IDs, Codes, and Timestamps) to prevent false positives.
3. **Completion:** The script will notify you in the terminal once all profiling and matching algorithms have finished.

---

## Output Artifacts and Interpretation

Upon completion, the engine generates three distinct artifacts. These files are automatically saved in the same folder where your Python scripts are located. 

### 1. Sweetviz_Data_Profile.html
* **What it is:** An interactive, high-density web dashboard for Exploratory Data Analysis. Open this file using any standard web browser (Chrome, Edge, Safari).
* **What it means:** This report provides an immediate statistical overview of your entire dataset. It highlights data distributions, flags missing or null values, and visualizes correlations between different columns. Use this to quickly assess the overall health and completeness of your raw data.

### 2. Fuzzy_Match_Results.csv
* **What it is:** A highly detailed audit table that exports directly to Excel or any CSV reader. This is the core output of the entity resolution engine.
* **What it means:** For every text column profiled, this table outlines:
  * **Canonical Name:** The master entity name chosen by the algorithm to represent a cluster of similar values.
  * **Total Count:** The aggregated frequency of the entity and all its captured variations combined.
  * **Variations Found:** The raw string values that the algorithm successfully identified as typos or duplicates and grouped together.
  * **Excel Row Numbers:** The exact row indices mapping back to your original source file (e.g., `4, 15, 202`). This guarantees total data lineage, allowing your team to trace exactly where a dirty data point originated.

### 3. Fuzzy_Impact_Histogram.png
* **What it is:** A high-resolution bar chart visualization comparing your data before and after processing.
* **What it means:** The blue bars represent the distinct count of items *before* fuzzy matching (which is often artificially high due to typos and formatting variations). The red bars represent the distinct count *after* fuzzy clustering. This chart provides immediate visual proof of how much "noise" the algorithm successfully removed from your dataset.

---

## Algorithmic Approach: The Levenshtein Distance

To achieve high-accuracy entity resolution, this engine utilizes the **Levenshtein Distance** algorithm (often referred to as Edit Distance) to evaluate textual similarities. 

Instead of relying on rigid, exact-text matches, the algorithm calculates the minimum number of single-character edits required to transform one string into another. These edits are classified as:
* **Insertions** (adding a missing letter)
* **Deletions** (removing an extra letter)
* **Substitutions** (swapping an incorrect letter for a correct one)

By analyzing these required edits relative to the total length of the strings, the engine generates a probabilistic similarity score. If the score meets our strict confidence threshold (defaulted to 70%), the engine dynamically clusters these variations under a single canonical entity. 

This mathematical approach allows the system to autonomously clean dirty data, standardize brand names, and deduplicate records without the need for manual oversight or hard-coded mapping rules.