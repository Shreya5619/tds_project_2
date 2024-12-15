import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib
import httpx
import argparse
import logging


# Set up logging for better error tracking
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Use a non-interactive backend to save plots without needing GUI interaction
matplotlib.use("Agg")  

# Ensure environment variable is set
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")
if not AIPROXY_TOKEN:
    logging.error("Error: AIPROXY_TOKEN is not set in the environment!")
    exit(1)

# API constants
API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
HEADERS = {
    'Authorization': f'Bearer {AIPROXY_TOKEN}',
    'Content-Type': 'application/json'
}

# Function to generate AI-based summary
def get_ai_summary(csv_file, data):
    """
    Request AI-based insights on the dataset for comprehensive analysis.
    """ 
    column_overview = ", ".join(data.columns)
    report_prompt = f"""
Create a detailed data analysis summary for the dataset {csv_file}. Columns include: {column_overview}. Provide insights on:
1. Dataset overview, including size and structure.
2. Key statistics (mean, median, unique values, missing data).
3. Trends and correlations (time-based and feature-based).
4. Visual insights and their implications.
5. Recommendations for further analysis or actions.
    """
    
    data_payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are an assistant generating concise data analysis summaries."},
            {"role": "user", "content": report_prompt}
        ],
    }

    try:
        response = httpx.post(API_URL, headers=HEADERS, json=data_payload, timeout=30.0)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        logging.error(f"Error in AI summary generation: {e}")
        return "AI summary generation failed."

# Save the AI-generated report
def save_report(csv_file, summary):
    report_filename = "README.md"
    try:
        with open(report_filename, "w") as f:
            f.write(f"# Data Analysis Report for {os.path.basename(csv_file)}\n")
            f.write(summary + "\n\n")
        logging.info(f"Report saved to {report_filename}")
    except Exception as e:
        logging.error(f"Error saving report: {e}")

# Create and save visualizations
def create_visualizations(csv_file, data):
    try:
        # Visualization: Top Genres by Average Rating
        if "Genre" in data.columns and "Rating" in data.columns:
            top_genres = data.groupby("Genre")["Rating"].mean().sort_values(ascending=False).head(5)
            sns.barplot(x=top_genres.index, y=top_genres.values, palette="viridis")
            plt.title(f"Top 5 Genres by Average Rating", fontsize=14)
            plt.xlabel("Genre", fontsize=12)
            plt.ylabel("Average Rating", fontsize=12)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f"{os.path.splitext(csv_file)[0]}_top_genres.png")
            plt.clf()

        # Correlation Heatmap
        numeric_data = data.select_dtypes(include=['number'])
        if not numeric_data.empty:
            corr = numeric_data.corr()
            sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
            plt.title("Correlation Heatmap", fontsize=14)
            plt.tight_layout()
            plt.savefig(f"{os.path.splitext(csv_file)[0]}_heatmap.png")
            plt.clf()

        # Yearly Trends
        if "Date" in data.columns:
            data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
            if not data['Date'].isna().all():
                data['Year'] = data['Date'].dt.year
                yearly_counts = data['Year'].value_counts().sort_index()
                sns.lineplot(x=yearly_counts.index, y=yearly_counts.values, marker="o")
                plt.title("Yearly Data Trends", fontsize=14)
                plt.xlabel("Year", fontsize=12)
                plt.ylabel("Counts", fontsize=12)
                plt.tight_layout()
                plt.savefig(f"{os.path.splitext(csv_file)[0]}_yearly_trends.png")
                plt.clf()
    except Exception as e:
        logging.error(f"Error creating visualizations: {e}")

# Process CSV file
def process_csv(csv_file):
    try:
        data = pd.read_csv(csv_file, encoding='ISO-8859-1')
        summary = get_ai_summary(csv_file, data)
        save_report(csv_file, summary)
        create_visualizations(csv_file, data)
    except Exception as e:
        logging.error(f"Error processing CSV file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a CSV file for data analysis.")
    parser.add_argument("csv_file", help="Path to the CSV file to process.")
    args = parser.parse_args()
    process_csv(args.csv_file)
    logging.info("Processing complete.")
