import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib
import httpx
import argparse

# Use a non-interactive backend to save plots without needing GUI interaction
matplotlib.use("Agg")  

# Set up the API key and proxy URL (This should be securely stored, for demo purposes it's here)
AIPROXY_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjIwMDI3NDJAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.TX-jkduQcB-9rTWd5rETbcSzqyPe9qUZsxhjMUnZWkM"

# Define the API URL and headers (Always use defined headers for secure and reusable code)
API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
HEADERS = {
    'Authorization': f'Bearer {AIPROXY_TOKEN}',
    'Content-Type': 'application/json'
}

# Function to generate AI-based summary (Modular, clear, and focused on data insights)
def get_ai_summary(csv_file, data):
    """
    Request AI-based insights on the dataset for comprehensive analysis.
    This modular function helps us to delegate AI communication and focus on visualization tasks separately.
    """ 
    report_prompt = f"""
Create a detailed data analysis summary for the dataset {csv_file}. Include the following sections:
1. **Overview**: Describe the dataset, including the number of rows, columns, and key variables.
2. **Key Statistics**:
    - Summary statistics for numeric columns (e.g., mean, median, standard deviation, etc.).
    - Unique value counts for categorical columns.
    - Detection of any missing or null values and how they are distributed across the columns.
3. **Trends and Insights**:
    - Analyze any trends over time (if a 'Date' or similar time-related column exists). Provide insights on how the data evolves across time.
    - Identify top-performing categories or groups, based on relevant metrics (e.g., views, engagement, sales).
4. **Correlation Analysis**:
    - Analyze the correlation between numeric variables and identify any strong correlations that might offer insights into relationships between features.
5. **Visual Insights**: Provide a description of what each visualization (such as correlation heatmap, trends, or category performance) indicates.
6. **Key Recommendations**:
    - Based on the data, what are some actionable insights or next steps that can be taken?
    - Suggest any further analysis that could be helpful (e.g., advanced statistical analysis, forecasting, segmentation).

Provide a concise yet thorough summary that highlights important findings, and structure the README as follows:

## Summary of Dataset
### 1. Overview
### 2. Key Statistics
### 3. Trends and Insights
### 4. Correlation Analysis
### 5. Visual Insights
### 6. Recommendations
"""
    
    # Define payload for the AI request
    data_payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are an assistant generating best and well structured data analysis summaries."},
            {"role": "user", "content": report_prompt}
        ],
    }

    try:
        response = httpx.post(API_URL, headers=HEADERS, json=data_payload, timeout=30.0)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except httpx.RequestError as e:
        return f"Request error occurred: {e}"
    except httpx.HTTPStatusError as e:
        return f"HTTP error occurred: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

# Function to save the AI-generated report (Isolating file-saving logic for better separation of concerns)
def save_report(csv_file, summary):
    """
    Save the AI-generated report to a markdown file.
    This ensures the output is both user-readable and structured.
    """
    report_filename = f"{os.path.splitext(csv_file)[0]}_README.md"
    with open(report_filename, "w") as f:
        f.write(f"# Data Analysis Report for {csv_file.capitalize()}\n")
        f.write("## Summary\n")
        f.write(summary + "\n\n")

# Function to create and save visualizations (One function for all related visualizations keeps logic clean)
def create_visualizations(csv_file, data):
    """
    Generate and save visualizations based on dataset columns.
    Each type of visualization (genre, correlation heatmap, and trends) is handled independently.
    """
    # Visualization: Top Genres by Average Rating
    if "Genre" in data.columns and "Rating" in data.columns:
        try:
            top_genres = data.groupby("Genre")["Rating"].mean().sort_values(ascending=False).head(5)
            sns.barplot(x=top_genres.index, y=top_genres.values, palette="viridis")
            plt.title(f"Top 5 Genres by Average Rating for {os.path.basename(csv_file)}", fontsize=14)
            plt.xlabel("Genre", fontsize=12)
            plt.ylabel("Average Rating", fontsize=12)
            plt.xticks(rotation=45)
            plt.tight_layout()

            output_path = f"{os.path.splitext(csv_file)[0]}_top_genres.png"
            plt.savefig(output_path)
            plt.clf()
        except Exception as e:
            print(f"Error creating genre visualization for {csv_file}: {e}")

    # Correlation Heatmap for numeric columns
    numeric_data = data.select_dtypes(include=['number'])
    if not numeric_data.empty:
        try:
            corr = numeric_data.corr()
            sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
            plt.title(f"Correlation Heatmap for {os.path.basename(csv_file)}", fontsize=14)
            plt.tight_layout()

            heatmap_filename = f"{os.path.splitext(csv_file)[0]}_heatmap.png"
            plt.savefig(heatmap_filename)
            plt.clf()
        except Exception as e:
            print(f"Error creating heatmap for {csv_file}: {e}")

    # Additional Visualizations (Yearly Trends)
    if "Date" in data.columns:
        try:
            data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
            if not data['Date'].isna().all():
                data.set_index('Date', inplace=True)
                data['Year'] = data.index.year
                yearly_counts = data['Year'].value_counts().sort_index()
                sns.lineplot(x=yearly_counts.index, y=yearly_counts.values, marker="o")
                plt.title(f"Yearly Data Trends for {os.path.basename(csv_file)}", fontsize=14)
                plt.xlabel("Year", fontsize=12)
                plt.ylabel("Counts", fontsize=12)
                plt.tight_layout()

                lineplot_filename = f"{os.path.splitext(csv_file)[0]}_yearly_trends.png"
                plt.savefig(lineplot_filename)
                plt.clf()
        except Exception as e:
            print(f"Error creating yearly trends visualization for {csv_file}: {e}")

# Main function to process the CSV file (Clear and concise, with separate concerns)
def process_csv(csv_file):
    """
    Main function for reading the CSV file, requesting AI summaries, generating visualizations,
    and saving all results.
    This ensures that the whole process is neatly isolated.
    """
    try:
        # Reading the data with proper encoding handling
        data = pd.read_csv(csv_file, encoding='ISO-8859-1')
    except UnicodeDecodeError:
        print(f"Error: Unable to read {csv_file} due to encoding issues.")
        return

    print(data.columns)
    print(data.head())

    # Generate the AI summary
    summary = get_ai_summary(csv_file, data)
    save_report(csv_file, summary)

    # Create and save visualizations
    create_visualizations(csv_file, data)

    print(f"Finished processing {csv_file}. Results saved.\n")

# Main script entry point (Robust argument handling and file processing)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a CSV file for data analysis.")
    parser.add_argument("csv_file", help="Path to the CSV file to process.")
    args = parser.parse_args()

    process_csv(args.csv_file)

    print("Processing complete.")
