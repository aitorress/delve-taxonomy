"""Test script for classifying work using predefined value streams taxonomy.

Usage:
    python test_value_streams.py <your_data.csv> <text_column_name>

Example:
    python test_value_streams.py traces.csv description
"""

import sys
from pathlib import Path
from delve import Delve

def main():
    # Check arguments
    if len(sys.argv) < 3:
        print("Usage: python test_value_streams.py <csv_file> <text_column>")
        print("\nExample:")
        print("  python test_value_streams.py traces.csv description")
        sys.exit(1)

    csv_file = sys.argv[1]
    text_column = sys.argv[2]

    # Validate CSV exists
    if not Path(csv_file).exists():
        print(f"Error: File '{csv_file}' not found")
        sys.exit(1)

    # Path to taxonomy (assumes this script is in examples/ folder)
    taxonomy_path = Path(__file__).parent / "value_streams_taxonomy.json"

    if not taxonomy_path.exists():
        print(f"Error: Taxonomy file not found at {taxonomy_path}")
        sys.exit(1)

    print("="*80)
    print("VALUE STREAMS CLASSIFICATION TEST")
    print("="*80)
    print(f"\nData file: {csv_file}")
    print(f"Text column: {text_column}")
    print(f"Taxonomy: {taxonomy_path}")
    print("\n" + "="*80 + "\n")

    # Initialize Delve with predefined taxonomy
    delve = Delve(
        predefined_taxonomy=str(taxonomy_path),
        verbose=True,
        output_dir="./results_value_streams",
        output_formats=["json", "csv", "markdown"]
    )

    # Run classification
    try:
        result = delve.run_sync(
            csv_file,
            text_column=text_column
        )

        # Print summary
        print("\n" + "="*80)
        print("CLASSIFICATION COMPLETE")
        print("="*80)

        print(f"\nUsed {len(result.taxonomy)} value stream categories:")
        for category in result.taxonomy:
            print(f"\n{category['id']}. {category['name']}")
            print(f"   {category['description'][:100]}...")

        print(f"\n\nLabeled {len(result.documents)} items")

        # Category distribution
        from collections import Counter
        category_counts = Counter(doc['category'] for doc in result.documents)

        print("\nDistribution by Value Stream:")
        for category, count in category_counts.most_common():
            percentage = (count / len(result.documents)) * 100
            print(f"  {category}: {count} ({percentage:.1f}%)")

        # Show some examples
        print("\n" + "="*80)
        print("SAMPLE CLASSIFICATIONS")
        print("="*80)

        for category in result.taxonomy:
            cat_name = category['name']
            examples = [doc for doc in result.documents if doc['category'] == cat_name][:2]

            if examples:
                print(f"\n{cat_name}:")
                for i, doc in enumerate(examples, 1):
                    preview = doc['content'][:150].replace('\n', ' ').strip()
                    print(f"  {i}. {preview}...")

        print("\n" + "="*80)
        print(f"Results saved to: ./results_value_streams/")
        print("="*80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
