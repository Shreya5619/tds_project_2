import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib
import httpx
import argparse

matplotlib.use("Agg")  # Use a non-interactive backend

# Set up the API key and proxy URL
AIPROXY_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjIwMDI3NDJAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.TX-jkduQcB-9rTWd5rETbcSzqyPe9qUZsxhjMUnZWkM"

# Function to process a single CSV file
def process_csv(csv_file):
    try:
        # Try reading the dataset with different encoding
        data = pd.read_csv(csv_file, encoding='ISO-8859-1')
    except UnicodeDecodeError:
        print(f"Error: Unable to read {csv_file} due to encoding issues.")
        return  # Skip if encoding fails

    print(data.columns)
    print(data.head())

    # AI Analysis - Generate summary for each CSV file
    API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    headers = {
        'Authorization': f'Bearer {AIPROXY_TOKEN}',
        'Content-Type': 'application/json'
    }
    report_prompt = f"""
    Create a summary of the dataset {csv_file}. Include:
    - Overview of key statistics
    - Top trends or correlations
    - Recommendations for next steps
    """

    data_payload = {
        "model": "gpt-4o-mini",
        "messages": [ 
            {"role": "system", "content": "You are an assistant generating data analysis summaries."},
            {"role": "user", "content": report_prompt}
        ],
    }

    try:
        response = httpx.post(API_URL, headers=headers, json=data_payload, timeout=30.0)
        response.raise_for_status()
        response_text = response.json()['choices'][0]['message']['content']
    except httpx.HTTPStatusError as e:
        response_text = f"HTTP error occurred: {e}"
    except httpx.RequestError as e:
        response_text = f"Request error occurred: {e}"
    except Exception as e:
        response_text = f"An unexpected error occurred: {e}"

    # Save the report for each dataset
    report_filename = f"{os.path.splitext(csv_file)[0]}_README.md"
    with open(report_filename, "w") as f:
        f.write(f"# Data Analysis Report for {csv_file.capitalize()}\n")
        f.write("## Summary\n")
        f.write(response_text + "\n\n")

    # Visualization: Enhanced Visualizations Section
    if "Genre" in data.columns and "Rating" in data.columns:
        try:
            top_genres = data.groupby("Genre")["Rating"].mean().sort_values(ascending=False).head(5)
            sns.barplot(x=top_genres.index, y=top_genres.values, palette="viridis")
            plt.title(f"Top 5 Genres by Average Rating for {os.path.basename(csv_file)}", fontsize=14)
            plt.xlabel("Genre", fontsize=12)
            plt.ylabel("Average Rating", fontsize=12)
            plt.xticks(rotation=45)
            plt.tight_layout()

            # Save the bar plot
            output_path = f"{os.path.splitext(csv_file)[0]}_top_genres.png"
            plt.savefig(output_path)
            plt.clf()
        except Exception as e:
            print(f"Error creating genre visualization for {csv_file}: {e}")
    else:
        print(f"Skipping top genres visualization for {csv_file} - 'Genre' or 'Rating' column missing.")

    # Correlation Heatmap for numeric columns (if applicable)
    numeric_data = data.select_dtypes(include=['number'])
    if not numeric_data.empty:
        try:
            corr = numeric_data.corr()
            sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
            plt.title(f"Correlation Heatmap for {os.path.basename(csv_file)}", fontsize=14)
            plt.tight_layout()

            # Save the heatmap
            heatmap_filename = f"{os.path.splitext(csv_file)[0]}_heatmap.png"
            plt.savefig(heatmap_filename)
            plt.clf()
        except Exception as e:
            print(f"Error creating heatmap for {csv_file}: {e}")
    else:
        print(f"Skipping correlation heatmap for {csv_file} - No numeric data available.")

    # Additional Visualizations (Optional):
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

                # Save the line plot
                lineplot_filename = f"{os.path.splitext(csv_file)[0]}_yearly_trends.png"
                plt.savefig(lineplot_filename)
                plt.clf()
        except Exception as e:
            print(f"Error creating yearly trends visualization for {csv_file}: {e}")

    print(f"Finished processing {csv_file}. Results saved for {csv_file}.\n")

# Main script entry point
if __name__ == "__main__":
    # Parse command-line argument for CSV file
    parser = argparse.ArgumentParser(description="Process a CSV file for data analysis.")
    parser.add_argument("csv_file", help="Path to the CSV file to process.")
    args = parser.parse_args()

    process_csv(args.csv_file)

    print("Processing complete for the dataset.")
