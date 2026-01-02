# @delve/client

JavaScript/TypeScript client for the Delve taxonomy generation API.

## Installation

```bash
npm install @delve/client
```

## Quick Start

```typescript
import { Delve } from '@delve/client';

// Connect to your Delve API
const delve = new Delve({
  apiUrl: 'https://your-delve-api.com'
});

// Generate taxonomy
const result = await delve.generate({
  documents: [
    { content: 'The app crashes when I click submit' },
    { content: 'Please add dark mode support' },
    { content: 'How do I reset my password?' },
  ],
  config: {
    max_num_clusters: 5,
    use_case: 'Categorize customer feedback',
  },
});

// Access results
console.log('Categories:', result.taxonomy);
console.log('Labeled docs:', result.labeled_documents);
```

## With Progress Updates

```typescript
const result = await delve.generate(
  {
    documents: myDocuments,
    config: { max_num_clusters: 5 },
  },
  (progress) => {
    console.log('Progress:', progress);
  }
);
```

## API Reference

### `new Delve(options)`

Create a new client instance.

```typescript
const delve = new Delve({
  apiUrl: 'https://your-api.com',  // Required
  timeout: 300000,                  // Optional: 5 min default
});
```

### `delve.generate(request, onProgress?)`

Generate taxonomy and label documents. Waits for completion.

```typescript
const result = await delve.generate({
  documents: [{ content: '...' }],
  config: {
    model: 'claude-sonnet-4-5-20250929',
    fast_llm: 'claude-haiku-4-5-20251001',
    sample_size: 100,
    batch_size: 200,
    max_num_clusters: 5,
    use_case: 'Categorize feedback',
  },
  // Optional: skip taxonomy discovery
  predefinedTaxonomy: [
    { id: '1', name: 'Bug', description: 'Bug reports' },
  ],
});
```

### `delve.createJob(request)`

Create a job without waiting for completion.

```typescript
const job = await delve.createJob({ documents: [...] });
console.log('Job ID:', job.job_id);
```

### `delve.getJob(jobId)`

Get job status and result.

```typescript
const job = await delve.getJob('job-id');
if (job.status === 'completed') {
  console.log(job.result);
}
```

### `delve.listJobs(options?)`

List all jobs.

```typescript
const { jobs, total } = await delve.listJobs({
  status: 'completed',
  limit: 10,
});
```

### `delve.deleteJob(jobId)`

Delete a job.

```typescript
await delve.deleteJob('job-id');
```

### `delve.healthCheck()`

Check API health.

```typescript
const isHealthy = await delve.healthCheck();
```

## Deploying Your Own API

See the [deployment guide](https://github.com/aitorress/delve-taxonomy#deployment) for instructions on deploying your own Delve API server.

## License

MIT
