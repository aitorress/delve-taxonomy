# @delve/taxonomy

AI-powered taxonomy generation for JavaScript and TypeScript.

## Installation

```bash
npm install @delve/taxonomy
```

## Quick Start

```typescript
import { Delve } from '@delve/taxonomy';

// Set your API key
process.env.ANTHROPIC_API_KEY = 'your-api-key';

// Create client
const delve = new Delve({
  maxNumClusters: 5,
  useCase: 'Categorize customer feedback',
});

// Generate taxonomy
const result = await delve.run([
  'The app crashes when I click submit',
  'Please add dark mode support',
  'How do I reset my password?',
]);

// Access results
console.log('Categories:', result.taxonomy);
console.log('Labeled docs:', result.labeledDocuments);
```

## API

### `new Delve(config?)`

Create a new Delve instance.

```typescript
const delve = new Delve({
  model: 'claude-sonnet-4-5-20250929',     // Main model for reasoning
  fastLlm: 'claude-haiku-4-5-20251001',    // Fast model for summarization
  sampleSize: 100,                          // Documents to sample
  batchSize: 200,                           // Batch size for clustering
  maxNumClusters: 5,                        // Max categories to generate
  useCase: 'Categorize feedback',           // Use case description
  anthropicApiKey: 'sk-...',                // Optional: API key
});
```

### `delve.run(documents, options?)`

Run taxonomy generation on documents.

```typescript
// Simple strings
const result = await delve.run([
  'Fix the login bug',
  'Add new feature',
]);

// Doc objects
const result = await delve.run([
  { id: '1', content: 'Fix the login bug' },
  { id: '2', content: 'Add new feature' },
]);

// With predefined taxonomy
const result = await delve.run(documents, {
  predefinedTaxonomy: [
    { id: '1', name: 'Bug', description: 'Bug reports' },
    { id: '2', name: 'Feature', description: 'Feature requests' },
  ],
});
```

### `generateTaxonomy(documents, config?)`

Convenience function for one-off taxonomy generation.

```typescript
import { generateTaxonomy } from '@delve/taxonomy';

const result = await generateTaxonomy([
  'Fix login bug',
  'Add dark mode',
], {
  useCase: 'Categorize software issues',
  maxNumClusters: 5,
});
```

## Result Structure

```typescript
interface DelveResult {
  taxonomy: TaxonomyCategory[];      // Generated categories
  labeledDocuments: Doc[];           // Documents with categories
  metadata: DelveMetadata;           // Run statistics
}

interface TaxonomyCategory {
  id: string;
  name: string;
  description: string;
}

interface Doc {
  id: string;
  content: string;
  category?: string;
  summary?: string;
}
```

## Environment Variables

```bash
# Required
export ANTHROPIC_API_KEY="your-anthropic-key"

# Optional (for classifier embeddings with large datasets)
export OPENAI_API_KEY="your-openai-key"
```

## License

MIT
