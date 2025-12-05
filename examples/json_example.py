"""JSON data source example for Delve.

This example demonstrates how to use Delve with JSON data,
including support for nested structures using JSONPath expressions.
"""

from delve import Delve
import json

def main():
    # Create sample JSON data
    sample_data = {
        "conversations": [
            {
                "id": "conv1",
                "messages": [
                    {"role": "user", "content": "How do I reset my password?"}
                ]
            },
            {
                "id": "conv2",
                "messages": [
                    {"role": "user", "content": "What are your pricing plans?"}
                ]
            },
            {
                "id": "conv3",
                "messages": [
                    {"role": "user", "content": "My app keeps crashing on startup"}
                ]
            }
        ]
    }

    # Save to file
    with open("sample_data.json", "w") as f:
        json.dump(sample_data, f, indent=2)

    # Initialize Delve
    delve = Delve(
        sample_size=50,
        output_dir="./json_results"
    )

    # Run with JSONPath to extract nested content
    print("Running taxonomy generation on JSON data...")
    result = delve.run_sync(
        "sample_data.json",
        json_path="$.conversations[*].messages[0].content"
    )

    # Display results
    print(f"\n✓ Generated {len(result.taxonomy)} categories")
    for category in result.taxonomy:
        # Get documents for this category
        category_docs = [
            doc for doc in result.labeled_documents
            if doc.category == category.name
        ]
        print(f"\n- {category.name}")
        print(f"  {category.description}")
        print(f"  Documents: {len(category_docs)}")

    print(f"\n✓ Results saved to: ./json_results/")

if __name__ == "__main__":
    main()
