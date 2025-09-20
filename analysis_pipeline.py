
import pandas as pd
from textblob import TextBlob
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime
from fpdf import FPDF

# --- Global constants for reporting ---
PDF_TITLE = "Resident Feedback Analysis: Q1-Q2 2025"
REPORT_DATE = datetime.now().strftime("%B %d, %Y")
CHART_DIR = 'reports/charts'

# --- 1. DATA PROCESSING ---
def load_and_process_data(filepath):
    """Loads and processes the feedback data."""
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        print(f"ERROR: Data file not found at '{filepath}'.")
        return None

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['topic'] = df['feedback_text'].apply(classify_topic)
    df['sentiment'] = df['feedback_text'].apply(get_sentiment)
    df['month'] = df['timestamp'].dt.to_period('M')
    return df

def classify_topic(text):
    """Classifies feedback into a department/topic using keyword matching."""
    text = text.lower()
    if any(kw in text for kw in ['park', 'playground', 'library', 'program', 'community center']): return 'Parks, Rec & Library'
    if any(kw in text for kw in ['trash', 'recycling', 'pickup', 'sweeping']): return 'Public Works - Sanitation'
    if any(kw in text for kw in ['pothole', 'road', 'traffic', 'street', 'crosswalk']): return 'Public Works - Transportation'
    if any(kw in text for kw in ['zoning', 'permit', 'construction', 'license']): return 'Community Development'
    if any(kw in text for kw in ['bill', 'main break', 'quality', 'sewer']): return 'Water Resources'
    if any(kw in text for kw in ['police', 'fire', 'officer', 'emergency']): return 'Public Safety'
    if any(kw in text for kw in ['yard', 'noise', 'vehicle']): return 'Code Enforcement'
    return 'General Inquiry'

def get_sentiment(text):
    """Analyzes the sentiment of a text string."""
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0.1: return 'Positive'
    if polarity < -0.1: return 'Negative'
    return 'Neutral'

# --- 2. VISUALIZATION ---
def create_visualizations(df):
    """Generates and saves all charts for the report."""
    os.makedirs(CHART_DIR, exist_ok=True)
    plt.style.use('seaborn-v0_8-whitegrid')

    # Chart 1: Comment Volume by Topic
    plt.figure(figsize=(10, 6))
    topic_counts = df['topic'].value_counts()
    sns.barplot(x=topic_counts.values, y=topic_counts.index, palette='viridis', hue=topic_counts.index, dodge=False, legend=False)
    plt.title('Total Feedback Volume by Department', fontsize=16)
    plt.xlabel('Number of Comments')
    plt.ylabel('')
    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/volume_by_topic.png')
    plt.close()

    # Chart 2: Sentiment Breakdown
    plt.figure(figsize=(10, 6))
    sentiment_by_topic = df.groupby('topic')['sentiment'].value_counts(normalize=True).unstack().fillna(0)
    sentiment_by_topic.plot(kind='barh', stacked=True, figsize=(10, 8), color=sns.color_palette("RdYlGn", 3))
    plt.title('Sentiment Breakdown by Department', fontsize=16)
    plt.xlabel('Proportion of Comments')
    plt.ylabel('')
    plt.legend(title='Sentiment', bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/sentiment_breakdown.png')
    plt.close()

    # Chart 3: Time Series of Comment Volume
    plt.figure(figsize=(12, 6))
    monthly_comments = df.set_index('timestamp')['feedback_text'].resample('M').count()
    monthly_comments.plot(kind='line', marker='o')
    plt.title('Monthly Feedback Volume (All Topics)', fontsize=16)
    plt.xlabel('Month')
    plt.ylabel('Number of Comments')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/volume_timeseries.png')
    plt.close()

# --- 3. PDF REPORTING ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, PDF_TITLE, 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 10, f'Report Generated: {REPORT_DATE}', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, text):
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 5, text)
        self.ln()

    def add_image(self, path, width_percent=0.8):
        page_width = self.w - 2 * self.l_margin
        img_width = page_width * width_percent
        self.image(path, x=self.get_x() + (page_width - img_width)/2, w=img_width)
        self.ln(5)

def generate_executive_summary(df):
    """Generates the text for the executive summary and recommendations."""
    total_comments = len(df)

    # Key Findings
    topic_counts = df['topic'].value_counts()
    most_common_topic = topic_counts.index[0]

    sentiment_counts = df['sentiment'].value_counts(normalize=True) * 100
    overall_positive = sentiment_counts.get('Positive', 0)

    neg_sentiment_by_topic = df[df['sentiment'] == 'Negative']['topic'].value_counts()
    worst_topic = neg_sentiment_by_topic.index[0]
    worst_topic_count = neg_sentiment_by_topic.iloc[0]

    monthly_volume = df.set_index('timestamp').resample('M').size()
    peak_month = monthly_volume.idxmax().strftime('%B')

    findings = f"""This report analyzes {total_comments} resident comments received between Jan 1 and Jun 30, 2025. The overall sentiment was {overall_positive:.1f}% positive.

- **Highest Feedback Volume:** '{most_common_topic}' was the most frequently discussed topic, indicating it is a primary area of resident interaction.

- **Primary Area of Concern:** '{worst_topic}' received the highest number of negative comments ({worst_topic_count}), suggesting a need for operational review and intervention.

- **Seasonal Trends:** Feedback volume peaked in {peak_month}, driven by seasonal issues. This predictability offers an opportunity for proactive resource allocation.
"""

    # Recommendations
    recommendations = f"""Based on the analysis, the following actions are recommended:

1.  **For the '{worst_topic}' Department:**
    - Conduct a root-cause analysis to understand the drivers of the {worst_topic_count} negative comments.
    - Develop a targeted action plan to address the most common complaints within this topic.
    - Launch a communications initiative to inform the public of planned improvements.

2.  **For the '{most_common_topic}' Department:**
    - Since this is a high-volume area, review communication channels and processes to ensure they are efficient and user-friendly.
    - Leverage the high interaction rate to gather more detailed feedback through targeted surveys.

3.  **Proactive Seasonal Planning:**
    - Allocate additional resources to address predictable seasonal peaks, such as increased road crews for post-winter repairs or groundskeepers for parks in the spring.
    - Use historical data to anticipate needs for the next quarter and set proactive performance goals.
"""
    return findings, recommendations

def create_pdf_report(df, findings, recommendations):
    """Assembles the final PDF report."""
    pdf = PDF()
    pdf.add_page()

    # Executive Summary
    pdf.chapter_title('1. Executive Summary & Key Findings')
    pdf.chapter_body(findings)

    # Recommendations
    pdf.chapter_title('2. Data-Driven Recommendations')
    pdf.chapter_body(recommendations)

    pdf.add_page()
    # Visualizations
    pdf.chapter_title('3. Visual Analysis')
    pdf.chapter_body('The following charts provide a visual breakdown of the feedback data.')

    pdf.add_image(f'{CHART_DIR}/volume_by_topic.png', 0.9)
    pdf.add_image(f'{CHART_DIR}/sentiment_breakdown.png', 0.9)
    pdf.add_image(f'{CHART_DIR}/volume_timeseries.png', 0.9)

    report_path = 'reports/Executive_Summary.pdf'
    pdf.output(report_path)
    return report_path

# --- 4. MAIN EXECUTION ---
def main():
    """Main function to run the full analysis and reporting pipeline."""
    print("--- Starting Resident Feedback Analysis Pipeline ---")

    df = load_and_process_data('sample_feedback.csv')
    if df is None:
        return

    print("Step 1: Data processed successfully.")

    create_visualizations(df)
    print("Step 2: Visualizations created.")

    findings, recommendations = generate_executive_summary(df)
    print("Step 3: Insights and recommendations generated.")

    report_path = create_pdf_report(df, findings, recommendations)
    print(f"Step 4: PDF report compiled successfully.")

    print(f"\n--- Pipeline Complete. Open '{report_path}' to view the summary. ---")

if __name__ == '__main__':
    main()
