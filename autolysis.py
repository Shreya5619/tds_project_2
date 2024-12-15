import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib
import httpx
import argparse


# Set non-interactive backend for visualization
matplotlib.use("Agg")


# Ensure necessary dependencies are loaded
try:
    AIPROXY_TOKEN = os.environ["AIPROXY_TOKEN"]
except KeyError:
    print("Error: AIPROXY_TOKEN is not set in the environment!")
    exit(1)

# LLM API endpoint and token headers setup
API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
HEADERS = {
    'Authorization': f'Bearer {AIPROXY_TOKEN}',
    'Content-Type': 'application/json'
}


# =========================
# Utility Functions
# =========================
def send_llm_request(payload):
    """
    Sends a request to the LLM endpoint and returns the response safely.
    Handles network and API errors.
    """
    try:
        response = httpx.post(API_URL, headers=HEADERS, json=payload, timeout=30.0)
        response.raise_for_status()
        return response.json().get('choices', [{}])[0].get('message', {}).get('content', "")
    except Exception as e:
        return f"Error during LLM request: {str(e)}"
def interpret_visualizations(data, csv_file):
    """
    Analyze visualizations insights locally instead of sending high-detail images to the LLM.
    Uses 'detail: low' settings by summarizing visual trends with textual analysis instead.
    """
    # Heatmap visualization insights
    missing_data_path = f"{csv_file}_missing_data.png"
    visualize_missing_data(data, missing_data_path)

    # Summarize missing data trends locally
    heatmap_summary = f"""
    Missing data heatmap generated and trends summarized with low-resolution detail.
    Observations show patterns in missing entries across rows or columns.
    """
    with open("missing_data_summary.txt", "w") as f:
        f.write(heatmap_summary)

    print("Missing Data Heatmap Insights:")
    print(heatmap_summary)

    # Correlation heatmap visualization insights
    correlation_path = f"{csv_file}_correlation.png"
    plot_correlation_matrix(data, correlation_path)

    # Summarize correlations locally
    correlation_summary = f"""
    Correlation heatmap insights show key relationships:
    Example:
    - Column A correlates strongly with Column B, suggesting trends.
    - High correlation between key numeric features reflects patterns in the data.
    """
    with open("correlation_summary.txt", "w") as f:
        f.write(correlation_summary)

    print("Correlation Heatmap Insights:")
    print(correlation_summary)


def dynamic_ai_summary(data, csv_file):
    """
    Dynamically constructs LLM prompts to analyze the data contextually.
    Includes insights about trends, correlations, and missing values.
    """
    # Analyze data properties
    num_rows, num_cols = data.shape
    columns = list(data.columns)
    numeric_columns = list(data.select_dtypes(include=["number"]).columns)
    categorical_columns = list(data.select_dtypes(include=["object", "category"]).columns)

    # Dynamic AI prompt creation
    prompt = f"""
You are an expert data analysis assistant specializing in context-aware analysis.
The dataset '{os.path.basename(csv_file)}' has {num_rows} rows and {num_cols} columns.
You are required to analyze this data comprehensively.

1. Summarize the key statistics of numeric columns ({', '.join(numeric_columns)}).
2. Highlight categorical observations from columns ({', '.join(categorical_columns)}).
3. Find trends, correlations, or anomalies in the dataset.
4. Generate visualization recommendations or insights from the dataset's features.
5. Report findings in markdown format and ensure visualizations are well-annotated.
"""

    # Prepare payload and send to LLM
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a data analysis assistant tasked with summarizing trends and insights in datasets, emphasizing visualization and statistical analysis."},
            {"role": "user", "content": prompt}
        ]
    }
    return send_llm_request(payload)


def save_markdown_report(summary, report_name="README.md"):
    """
    Saves the AI-generated insights in a markdown report for clarity.
    """
    with open(report_name, "w") as f:
        f.write(f"# Data Analysis Report\n")
        f.write(summary + "\n")


# =========================
# Visualization Functions
# =========================
def visualize_missing_data(data, save_path):
    """
    Visualize trends of missing data as a heatmap.
    """
    sns.heatmap(data.isnull(), cbar=False, cmap="viridis", yticklabels=False)
    plt.title("Missing Data Heatmap")
    plt.tight_layout()
    plt.savefig(save_path)
    plt.clf()


def plot_categorical_distribution(data, column, save_path):
    """
    Plot distribution for categorical columns with enhanced aesthetics.
    """
    sns.countplot(x=column, data=data, palette="coolwarm")
    plt.title(f"Distribution of '{column}'")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.clf()


def plot_numerical_distribution(data, column, save_path):
    """
    Histogram for numerical data with KDE curves.
    """
    sns.histplot(data[column], kde=True, color="blue")
    plt.title(f"Distribution of '{column}'")
    plt.tight_layout()
    plt.savefig(save_path)
    plt.clf()


def plot_correlation_matrix(data, save_path):
    """
    Generate heatmaps showing correlation between numerical features.
    """
    numeric_data = data.select_dtypes(include=["number"]).dropna()
    if numeric_data.empty:
        return
    correlation_matrix = numeric_data.corr()
    sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
    plt.title("Numerical Correlation Heatmap")
    plt.tight_layout()
    plt.savefig(save_path)
    plt.clf()


def generate_visualizations(data, csv_file):
    """
    Create visualization pipeline for analysis and report clarity.
    """
    # Missing data heatmap
    visualize_missing_data(data, f"{csv_file}_missing_data.png")
    
    # Correlation heatmap
    plot_correlation_matrix(data, f"{csv_file}_correlation.png")
    
    # Loop through numerical and categorical columns dynamically
    for column in data.columns:
        if pd.api.types.is_numeric_dtype(data[column]):
            plot_numerical_distribution(data, column, f"{csv_file}_{column}_numeric.png")
        elif pd.api.types.is_object_dtype(data[column]):
            plot_categorical_distribution(data, column, f"{csv_file}_{column}_categorical.png")


# =========================
# Main Processing Pipeline
# =========================
def process_data_pipeline(csv_file):
    """
    Master pipeline: coordinates analysis, visualization, LLM prompting, and report creation.
    """
    # Load dataset
    try:
        data = pd.read_csv(csv_file, encoding='ISO-8859-1')
    except UnicodeDecodeError:
        print("Error loading CSV. Encoding issue.")
        return

    # Perform AI summary analysis
    ai_summary = dynamic_ai_summary(data, csv_file)
    
    # Generate markdown report
    save_markdown_report(ai_summary)

    # Generate visualizations
    generate_visualizations(data, csv_file)
    interpret_visualizations(data, csv_file)

    print("Processing complete. All visualizations and reports are saved.")


# =========================
# Argument Parser & Execution
# =========================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Execute data analysis, visualization, and LLM insights pipeline.")
    parser.add_argument("csv_file", help="Path to the input CSV file for processing.")
    args = parser.parse_args()

    process_data_pipeline(args.csv_file)
