"""Basic CSV usage example for Delve.

This example demonstrates how to use Delve to generate a taxonomy
from a CSV file with a simple text column.
"""

from delve import Delve

def main():
    # Initialize Delve client with default settings
    delve = Delve(
        model="anthropic/claude-3-5-sonnet-20241022",
        sample_size=100,
        output_dir="./results"
    )

    # Run taxonomy generation on a CSV file
    print("Running taxonomy generation...")
    result = delve.run_sync(
        "sample_data.csv",
        text_column="text"
    )

    # Display results
    print(f"\n✓ Generated {len(result.taxonomy)} categories!")
    print("\nCategories:")
    for i, category in enumerate(result.taxonomy, 1):
        # Get documents for this category
        category_docs = [
            doc for doc in result.labeled_documents
            if doc.category == category.name
        ]
        print(f"\n{i}. {category.name}")
        print(f"   Description: {category.description}")
        print(f"   Documents: {len(category_docs)}")

    # Show some labeled documents
    print("\nSample labeled documents:")
    for doc in result.labeled_documents[:5]:
        print(f"\n- ID: {doc.id}")
        print(f"  Category: {doc.category}")
        print(f"  Content: {doc.content[:100]}...")
        print(f"  Explanation: {doc.explanation}")

    print(f"\n✓ Results saved to: ./results/")

if __name__ == "__main__":
    main()
