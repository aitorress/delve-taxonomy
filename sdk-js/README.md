# @delve-ai/taxonomy

TypeScript/JavaScript client SDK for the Delve Taxonomy API - AI-powered taxonomy generation using LLMs.

## Installation

```bash
npm install @delve-ai/taxonomy
# or
yarn add @delve-ai/taxonomy
# or
pnpm add @delve-ai/taxonomy
```

## Prerequisites

You need a running Delve API server. See the [API documentation](../docs/api-reference.mdx) for setup instructions.

```bash
# Start the API server
pip install delve-taxonomy fastapi uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Quick Start

```typescript
import { Delve } from '@delve-ai/taxonomy';

// Create client
const delve = new Delve({
  baseUrl: 'http://localhost:8000'
});

// Generate taxonomy from array of objects
const result = await delve.generateFromArray(
  [
    { text: 'How do I reset my password?' },
    { text: 'Billing question about my invoice' },
    { text: 'Bug report: app crashes on startup' }
  ],
  {
    textField: 'text',
    config: { maxNumClusters: 5 }
  }
);

console.log('Generated Taxonomy:');
result.taxonomy.forEach(cat => {
  console.log(`- ${cat.name}: ${cat.description}`);
});
```

## Methods

### generateFromArray(data, options)

Generate taxonomy from an array of data objects.

```typescript
const result = await delve.generateFromArray(
  [{ message: 'Help needed' }, { message: 'Feature request' }],
  { textField: 'message', config: { maxNumClusters: 5 } }
);
```

### generateFromDocuments(documents, options)

Generate taxonomy from pre-formatted Document objects.

```typescript
const result = await delve.generateFromDocuments([
  { id: '1', content: 'Customer support inquiry' },
  { id: '2', content: 'Technical question' }
]);
```

### generateFromCSV(csvContent, options)

Generate taxonomy from CSV content.

```typescript
const csv = `id,message\n1,Login help\n2,Billing issue`;
const result = await delve.generateFromCSV(csv, {
  textColumn: 'message',
  idColumn: 'id'
});
```

### generateFromJSON(jsonContent, options)

Generate taxonomy from JSON or JSONL content.

```typescript
const json = JSON.stringify([{ text: 'Question 1' }, { text: 'Question 2' }]);
const result = await delve.generateFromJSON(json, { textField: 'text' });
```

### labelDocuments(documents, taxonomy, options)

Label documents using an existing taxonomy.

```typescript
const taxonomy = [
  { id: '1', name: 'Support', description: 'Customer support' },
  { id: '2', name: 'Billing', description: 'Payment questions' }
];

const result = await delve.labelDocuments(
  [{ id: 'new1', content: 'Need help with subscription' }],
  taxonomy
);
```

## Configuration

```typescript
const delve = new Delve({
  baseUrl: 'http://localhost:8000',
  headers: { 'Authorization': 'Bearer token' },
  timeout: 300000  // 5 minutes
});
```

### Generation Config

```typescript
const result = await delve.generateFromArray(data, {
  textField: 'text',
  config: {
    model: 'anthropic/claude-sonnet-4-5-20250929',
    sampleSize: 100,
    batchSize: 200,
    maxNumClusters: 5,
    useCase: 'Categorize customer feedback'
  }
});
```

## Error Handling

```typescript
import { DelveError } from '@delve-ai/taxonomy';

try {
  const result = await delve.generateFromArray(data);
} catch (error) {
  if (error instanceof DelveError) {
    console.error('Error:', error.message);
    console.error('Status:', error.status);
  }
}
```

## Types

The SDK provides full TypeScript support:

```typescript
import {
  Delve,
  DelveConfig,
  DelveResult,
  Document,
  LabeledDocument,
  TaxonomyCategory,
  DelveError
} from '@delve-ai/taxonomy';
```

## License

MIT
