"""Example: Using a predefined taxonomy with Delve.

This example demonstrates how to use Delve with a predefined taxonomy
instead of discovering categories from scratch.
"""

from delve import Delve

# Example 1: Using a predefined taxonomy as a Python list
predefined_categories = [
    {
        "id": "1",
        "name": "Technical Support",
        "description": "Issues related to technical problems, bugs, or system errors"
    },
    {
        "id": "2",
        "name": "Billing and Payments",
        "description": "Questions about invoices, payment methods, refunds, or pricing"
    },
    {
        "id": "3",
        "name": "Feature Requests",
        "description": "Requests for new features or enhancements to existing functionality"
    },
    {
        "id": "4",
        "name": "Account Management",
        "description": "Issues related to account settings, authentication, or user profile"
    },
]

# Initialize Delve with predefined taxonomy
delve = Delve(
    predefined_taxonomy=predefined_categories,
    sample_size=50,  # Process 50 documents
    verbose=True
)

# Run on your data - it will skip discovery and go straight to labeling
result = delve.run_sync(
    "sample_data.csv",
    text_column="text"
)

# Access results
print("\n" + "="*80)
print("PREDEFINED TAXONOMY RESULTS")
print("="*80)

print(f"\nUsed {len(result.taxonomy)} predefined categories:")
for category in result.taxonomy:
    print(f"  - {category['name']}: {category['description']}")

print(f"\nLabeled {len(result.documents)} documents")

# Show some examples
print("\nSample labeled documents:")
for i, doc in enumerate(result.documents[:5]):
    preview = doc['content'][:100].replace('\n', ' ')
    print(f"\n{i+1}. Category: {doc['category']}")
    print(f"   Content: {preview}...")


# Example 2: Load taxonomy from a file
# You can also load from JSON or CSV files:
#
# delve = Delve(predefined_taxonomy="taxonomy.json")
# delve = Delve(predefined_taxonomy="taxonomy.csv")
#
# JSON format should be a list of objects:
# [
#   {"id": "1", "name": "Category 1", "description": "..."},
#   {"id": "2", "name": "Category 2", "description": "..."}
# ]
#
# CSV format should have columns: id, name, description
