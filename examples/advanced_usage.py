"""Advanced usage example for Delve.

This example demonstrates advanced features like:
- Custom use cases
- Async API usage
- Processing large datasets
- Custom output formats
- Programmatic result access
"""

import asyncio
from delve import Delve
import pandas as pd

async def async_example():
    """Example using async API."""
    print("=== Async API Example ===\n")

    delve = Delve(
        use_case="Categorize customer feedback into product areas",
        sample_size=150,
        batch_size=50,
        output_dir="./async_results",
        output_formats=["json", "markdown"]  # Only JSON and Markdown
    )

    # Use async API
    result = await delve.run(
        "sample_data.csv",
        text_column="text"
    )

    print(f"✓ Generated {len(result.taxonomy)} categories\n")

def custom_configuration_example():
    """Example with custom configuration."""
    print("=== Custom Configuration Example ===\n")

    delve = Delve(
        model="anthropic/claude-3-5-sonnet-20241022",
        fast_llm="anthropic/claude-3-haiku-20240307",
        use_case="Analyze support tickets to identify common issues",
        sample_size=200,
        batch_size=100,
        output_dir="./custom_results",
        verbose=True
    )

    result = delve.run_sync(
        "sample_data.csv",
        text_column="text"
    )

    print(f"\n✓ Processed with custom settings\n")

def programmatic_access_example():
    """Example showing programmatic result access."""
    print("=== Programmatic Access Example ===\n")

    delve = Delve(sample_size=100, output_dir="./programmatic_results")
    result = delve.run_sync("sample_data.csv", text_column="text")

    # Access taxonomy
    print("Taxonomy categories:")
    for category in result.taxonomy:
        # Get documents for this category
        category_docs = [
            doc for doc in result.labeled_documents
            if doc.category == category.name
        ]
        print(f"\n{category.name}:")
        print(f"  Description: {category.description}")
        print(f"  Document count: {len(category_docs)}")

        # Show sample documents
        if category_docs:
            print(f"  Sample document: {category_docs[0].content[:100]}...")

    # Calculate statistics
    total_docs = len(result.labeled_documents)
    avg_docs_per_category = total_docs / len(result.taxonomy) if result.taxonomy else 0

    print(f"\n\nStatistics:")
    print(f"  Total documents: {total_docs}")
    print(f"  Total categories: {len(result.taxonomy)}")
    print(f"  Avg docs per category: {avg_docs_per_category:.1f}")

def large_dataset_example():
    """Example for processing large datasets."""
    print("=== Large Dataset Example ===\n")

    # Create large sample dataset
    large_df = pd.DataFrame({
        "id": [f"doc{i}" for i in range(1000)],
        "text": [f"Sample document text {i}" for i in range(1000)]
    })

    # Save to CSV
    large_df.to_csv("large_dataset.csv", index=False)

    # Process with larger sample size
    delve = Delve(
        sample_size=300,  # Sample 300 documents
        batch_size=50,    # Process in smaller batches
        output_dir="./large_results"
    )

    result = delve.run_sync(
        "large_dataset.csv",
        text_column="text",
        id_column="id"
    )

    print(f"✓ Processed large dataset")
    print(f"  Sampled: 300 from 1000 documents")
    print(f"  Generated: {len(result.taxonomy)} categories\n")

def main():
    """Run all examples."""
    print("Delve Advanced Usage Examples\n")
    print("=" * 50 + "\n")

    # Run sync examples
    custom_configuration_example()
    programmatic_access_example()
    large_dataset_example()

    # Run async example
    asyncio.run(async_example())

    print("\n" + "=" * 50)
    print("✓ All examples completed!")

if __name__ == "__main__":
    main()
