"""Pandas DataFrame example for Delve.

This example demonstrates how to use Delve directly with
pandas DataFrames for in-memory processing.
"""

import pandas as pd
from delve import Delve

def main():
    # Create sample DataFrame
    data = {
        "id": ["doc1", "doc2", "doc3", "doc4", "doc5"],
        "text": [
            "How do I reset my password?",
            "What are your pricing plans?",
            "My app keeps crashing on startup",
            "Do you offer enterprise support?",
            "I'm getting an error message when I login"
        ],
        "metadata": ["support", "sales", "support", "sales", "support"]
    }
    df = pd.DataFrame(data)

    print("Sample DataFrame:")
    print(df)
    print()

    # Initialize Delve
    delve = Delve(
        use_case="Categorize customer inquiries",
        sample_size=50,
        output_dir="./dataframe_results"
    )

    # Run directly on DataFrame
    print("Running taxonomy generation...")
    result = delve.run_sync(
        df,
        text_column="text",
        id_column="id"
    )

    # Create results DataFrame
    results_df = pd.DataFrame([
        {
            "id": doc.id,
            "original_text": doc.content,
            "category": doc.category,
            "explanation": doc.explanation
        }
        for doc in result.labeled_documents
    ])

    print("\nResults DataFrame:")
    print(results_df)

    # Show category distribution
    print("\nCategory Distribution:")
    print(results_df["category"].value_counts())

    print(f"\n✓ Results saved to: ./dataframe_results/")

if __name__ == "__main__":
    main()
