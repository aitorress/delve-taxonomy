"""Test script for classifying Jira issues using value streams taxonomy.

This script:
1. Reads your Jira CSV
2. Combines 'summary' and 'description' columns for better context
3. Classifies each issue into value streams
4. Saves results with the original Jira data preserved
"""

from pathlib import Path
import pandas as pd
from delve import Delve

def main():
    # Input file (assuming it's in the root directory)
    csv_file = "jira_issues_2025_H64_20251215_135442.csv"

    if not Path(csv_file).exists():
        print(f"Error: File '{csv_file}' not found")
        print(f"Looking in: {Path.cwd()}")
        return

    print("="*80)
    print("JIRA ISSUES VALUE STREAM CLASSIFICATION")
    print("="*80)
    print(f"\nReading Jira issues from: {csv_file}")

    # Read the CSV
    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} issues")

    # Create combined text column (summary + description)
    print("\nCombining 'summary' and 'description' columns for better context...")
    df['combined_text'] = df.apply(
        lambda row: f"{row['summary']}\n\n{row['description']}"
        if pd.notna(row['description']) and str(row['description']).strip()
        else str(row['summary']),
        axis=1
    )

    # Save preprocessed version temporarily
    temp_file = "temp_jira_preprocessed.csv"
    df[['key', 'combined_text']].to_csv(temp_file, index=False)

    # Path to taxonomy
    taxonomy_path = Path("examples/value_streams_taxonomy.json")
    if not taxonomy_path.exists():
        print(f"Error: Taxonomy file not found at {taxonomy_path}")
        return

    print(f"Using taxonomy: {taxonomy_path}")
    print("\n" + "="*80 + "\n")

    # Initialize Delve with predefined taxonomy
    # Using sample_size=100 means:
    # - LLM labels 100 documents (high quality)
    # - Trains classifier on those 100
    # - Classifier labels remaining documents (fast & cheap)
    delve = Delve(
        predefined_taxonomy=str(taxonomy_path),
        sample_size=100,  # LLM labels this many, classifier does the rest
        verbose=True,
        output_dir="./results_jira_value_streams",
        output_formats=["json", "csv", "markdown"],
        embedding_model="text-embedding-3-large"
    )

    # Run classification
    try:
        result = delve.run_sync(
            temp_file,
            text_column="combined_text",
            id_column="key"
        )

        # Clean up temp file
        Path(temp_file).unlink()

        # Merge results back with original Jira data
        print("\nMerging classifications with original Jira data...")

        # Convert Doc objects to DataFrame
        result_data = [
            {'id': doc.id, 'category': doc.category}
            for doc in result.labeled_documents
        ]
        result_df = pd.DataFrame(result_data)

        # Merge on the document ID (which should be the Jira key)
        merged_df = df.merge(
            result_df,
            left_on='key',
            right_on='id',
            how='left'
        )

        # Drop columns that we don't need (check if they exist first)
        cols_to_drop = []
        if 'id' in merged_df.columns and 'id' != 'key':
            cols_to_drop.append('id')
        if 'combined_text' in merged_df.columns:
            cols_to_drop.append('combined_text')

        if cols_to_drop:
            merged_df = merged_df.drop(columns=cols_to_drop)

        # Save enhanced CSV with classifications
        output_csv = "results_jira_value_streams/jira_issues_classified.csv"
        Path("results_jira_value_streams").mkdir(exist_ok=True)
        merged_df.to_csv(output_csv, index=False)

        # Print summary
        print("\n" + "="*80)
        print("CLASSIFICATION COMPLETE")
        print("="*80)

        print(f"\nClassified {len(result.labeled_documents)} issues into {len(result.taxonomy)} value streams")

        # Category distribution
        from collections import Counter
        category_counts = Counter(doc.category for doc in result.labeled_documents)

        print("\n📊 Distribution by Value Stream:")
        print("-" * 80)
        for category, count in category_counts.most_common():
            percentage = (count / len(result.labeled_documents)) * 100
            bar = "█" * int(percentage / 2)  # Simple bar chart
            print(f"{category:50s} {count:4d} ({percentage:5.1f}%) {bar}")

        # Show examples for each category
        print("\n" + "="*80)
        print("SAMPLE CLASSIFICATIONS")
        print("="*80)

        for category in result.taxonomy:
            cat_name = category.name
            examples = [doc for doc in result.labeled_documents if doc.category == cat_name][:3]

            if examples:
                print(f"\n📌 {cat_name} ({len([d for d in result.labeled_documents if d.category == cat_name])} issues)")
                print("-" * 80)
                for i, doc in enumerate(examples, 1):
                    # Get the original Jira issue
                    jira_issue = merged_df[merged_df['key'] == doc.id].iloc[0]
                    summary = jira_issue['summary'][:100]
                    print(f"  {doc.id}: {summary}")

        print("\n" + "="*80)
        print("📁 RESULTS SAVED")
        print("="*80)
        print(f"  • Full results: ./results_jira_value_streams/")
        print(f"  • Classified CSV: {output_csv}")
        print("="*80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        # Clean up temp file on error
        if Path(temp_file).exists():
            Path(temp_file).unlink()

if __name__ == "__main__":
    main()
