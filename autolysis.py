import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os

import openai
import matplotlib
matplotlib.use("Agg")  

load_dotenv()
# Set up the API key and proxy URL
openai.api_key = os.getenv("API_TOKEN")  # Secure setup (best practice)
openai.api_base = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

# List of CSV files to process
CSV_FILES = ["goodreads.csv", "happiness.csv", "media.csv"]

# Process Each CSV File
for csv_file in CSV_FILES:
    print(f"Processing {csv_file}...")
    
    try:
        # Try reading the dataset with different encoding
        data = pd.read_csv(csv_file, encoding='ISO-8859-1')  # Try 'ISO-8859-1' or 'latin1'
    except UnicodeDecodeError:
        print(f"Error: Unable to read {csv_file} due to encoding issues.")
        continue  # Skip to the next file if encoding fails

    # AI Analysis - Generate summary for each CSV file
    report_prompt = f"""
    Create a summary of the dataset {csv_file}. Include:
    - Overview of key statistics
    - Top trends or correlations
    - Recommendations for next steps
    """

    openai.api_base = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
   # Initialize the OpenAI client with your API key and base URL
    client = openai.OpenAI(
        api_key=os.getenv("API_TOKEN"),  # Fetch the API token securely from environment variables
        #api_base="https://aiproxy.sanand.workers.dev/openai/v1/chat/completions",  # Your custom API base URL
    )
    chat_completion = client.chat.completions.create(
        model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an assistant generating data analysis summaries."},
                    {"role": "user", "content": report_prompt},
                ],
                max_tokens=300,
                temperature=0.7 
)
# Usage Example
    report_text = chat_completion(report_prompt)

    # Save the report for each dataset
    report_filename = f"{os.path.splitext(csv_file)[0]}_README.md"
    with open(report_filename, "w") as f:
        f.write(f"# Data Analysis Report for {csv_file.capitalize()}\n")
        f.write("## Summary\n")
        f.write(report_text + "\n\n")

    # Visualization: Top Genres or Any Relevant Columns (if applicable)
    if "Genre" in data.columns and "Rating" in data.columns:
        top_genres = data.groupby("Genre")["Rating"].mean().sort_values(ascending=False).head(5)
        sns.barplot(x=top_genres.index, y=top_genres.values)
        plt.title(f"Top 5 Genres by Average Rating for {csv_file}")
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save the bar plot for each dataset
        output_path = f"{os.path.splitext(csv_file)[0]}_top_genres.png"
        plt.savefig(output_path)
        plt.clf()  # Clear the plot for the next iteration
    else:
        print(f"Skipping top genres visualization for {csv_file} - 'Genre' or 'Rating' column missing.")    

    # Correlation Heatmap for numeric columns (if applicable)
    numeric_data = data.select_dtypes(include=['number'])
    if not numeric_data.empty:
        corr = numeric_data.corr()
        sns.heatmap(corr, annot=True, cmap="coolwarm")
        plt.title(f"Correlation Heatmap for {csv_file}")
        plt.tight_layout()
        
        # Save the heatmap for each dataset
        heatmap_filename = f"{os.path.splitext(csv_file)[0]}_heatmap.png"
        plt.savefig(heatmap_filename)
        plt.clf()  # Clear the plot for the next iteration

    print(f"Finished processing {csv_file}. Results saved for {csv_file}.\n")

print("Processing complete for all datasets.")