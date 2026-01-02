/**
 * @delve/client - JavaScript/TypeScript client for Delve API
 *
 * A thin wrapper around the Delve REST API that provides a clean,
 * type-safe interface for taxonomy generation.
 *
 * @example
 * ```typescript
 * import { Delve } from '@delve/client';
 *
 * const delve = new Delve({ apiUrl: 'https://your-delve-api.com' });
 *
 * const result = await delve.generate({
 *   documents: [
 *     { content: 'Fix the login bug' },
 *     { content: 'Add dark mode support' },
 *   ],
 *   config: { maxNumClusters: 5 },
 * });
 *
 * console.log(result.taxonomy);
 * ```
 */

// =============================================================================
// Types
// =============================================================================

export type JobStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface TaxonomyCategory {
  id: string;
  name: string;
  description: string;
}

export interface LabeledDocument {
  id: string;
  content: string;
  category: string | null;
  summary: string | null;
  explanation: string | null;
}

export interface ClassifierMetrics {
  train_accuracy: number;
  test_accuracy: number;
  train_f1: number;
  test_f1: number;
}

export interface ResultMetadata {
  num_documents: number;
  num_categories: number;
  sample_size: number;
  batch_size: number;
  model: string;
  fast_llm: string;
  run_duration_seconds: number;
  category_counts: Record<string, number>;
  llm_labeled_count: number;
  classifier_labeled_count: number;
  skipped_document_count: number;
  classifier_metrics?: ClassifierMetrics;
  warnings: string[];
}

export interface TaxonomyResult {
  taxonomy: TaxonomyCategory[];
  labeled_documents: LabeledDocument[];
  metadata: ResultMetadata;
}

export interface Job {
  job_id: string;
  status: JobStatus;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  progress: string | null;
  error: string | null;
  result: TaxonomyResult | null;
}

export interface TaxonomyConfig {
  model?: string;
  fast_llm?: string;
  sample_size?: number;
  batch_size?: number;
  max_num_clusters?: number;
  use_case?: string;
  embedding_model?: string;
  classifier_confidence_threshold?: number;
}

export interface InlineDocument {
  id?: string;
  content: string;
}

export interface PredefinedCategory {
  id: string;
  name: string;
  description: string;
}

export interface GenerateRequest {
  /** Documents to categorize */
  documents: InlineDocument[];
  /** Taxonomy generation configuration */
  config?: TaxonomyConfig;
  /** Use predefined categories instead of generating */
  predefinedTaxonomy?: PredefinedCategory[];
}

export interface ProgressCallback {
  (message: string): void;
}

export interface DelveOptions {
  /** Base URL of the Delve API */
  apiUrl: string;
  /** Request timeout in milliseconds (default: 300000 = 5 min) */
  timeout?: number;
}

// =============================================================================
// Client
// =============================================================================

/**
 * Delve API client for taxonomy generation.
 *
 * @example
 * ```typescript
 * const delve = new Delve({
 *   apiUrl: 'https://your-delve-api.com'
 * });
 *
 * // Generate taxonomy
 * const result = await delve.generate({
 *   documents: [{ content: 'Bug report' }, { content: 'Feature request' }],
 *   config: { max_num_clusters: 5 }
 * });
 * ```
 */
export class Delve {
  private apiUrl: string;
  private timeout: number;

  constructor(options: DelveOptions) {
    this.apiUrl = options.apiUrl.replace(/\/$/, ''); // Remove trailing slash
    this.timeout = options.timeout ?? 300000;
  }

  /**
   * Generate taxonomy and label documents.
   *
   * This method creates a job, polls for completion, and returns the result.
   * For long-running jobs, use `createJob` + `streamProgress` instead.
   */
  async generate(
    request: GenerateRequest,
    onProgress?: ProgressCallback
  ): Promise<TaxonomyResult> {
    const job = await this.createJob(request);

    if (onProgress) {
      return this.waitWithProgress(job.job_id, onProgress);
    }

    return this.waitForCompletion(job.job_id);
  }

  /**
   * Create a taxonomy generation job.
   */
  async createJob(request: GenerateRequest): Promise<Job> {
    const body: Record<string, unknown> = {
      documents: request.documents,
    };

    if (request.config) {
      body.config = request.config;
    }

    if (request.predefinedTaxonomy) {
      body.predefined_taxonomy = request.predefinedTaxonomy;
    }

    const response = await fetch(`${this.apiUrl}/taxonomies`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || error.error || `API error: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Get job status and result.
   */
  async getJob(jobId: string): Promise<Job> {
    const response = await fetch(`${this.apiUrl}/taxonomies/${jobId}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Job ${jobId} not found`);
      }
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || error.error || `API error: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Wait for job completion by polling.
   */
  async waitForCompletion(
    jobId: string,
    pollInterval = 2000
  ): Promise<TaxonomyResult> {
    const startTime = Date.now();

    while (true) {
      if (Date.now() - startTime > this.timeout) {
        throw new Error(`Job ${jobId} timed out after ${this.timeout}ms`);
      }

      const job = await this.getJob(jobId);

      if (job.status === 'completed' && job.result) {
        return job.result;
      }

      if (job.status === 'failed') {
        throw new Error(job.error || 'Job failed');
      }

      await sleep(pollInterval);
    }
  }

  /**
   * Wait for job with progress updates via SSE.
   */
  async waitWithProgress(
    jobId: string,
    onProgress: ProgressCallback
  ): Promise<TaxonomyResult> {
    return new Promise((resolve, reject) => {
      const eventSource = new EventSource(
        `${this.apiUrl}/taxonomies/${jobId}/stream`
      );

      const timeout = setTimeout(() => {
        eventSource.close();
        reject(new Error(`Job ${jobId} timed out`));
      }, this.timeout);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          switch (data.event) {
            case 'progress':
              onProgress(data.message || 'Processing...');
              break;
            case 'completed':
              clearTimeout(timeout);
              eventSource.close();
              resolve(data.result);
              break;
            case 'error':
              clearTimeout(timeout);
              eventSource.close();
              reject(new Error(data.error || 'Job failed'));
              break;
          }
        } catch (e) {
          // Ignore parse errors for keepalive messages
        }
      };

      eventSource.onerror = () => {
        clearTimeout(timeout);
        eventSource.close();
        // Fall back to polling on SSE error
        this.waitForCompletion(jobId).then(resolve).catch(reject);
      };
    });
  }

  /**
   * List all jobs.
   */
  async listJobs(options?: {
    status?: JobStatus;
    limit?: number;
    offset?: number;
  }): Promise<{ jobs: Job[]; total: number }> {
    const params = new URLSearchParams();
    if (options?.status) params.set('status', options.status);
    if (options?.limit) params.set('limit', String(options.limit));
    if (options?.offset) params.set('offset', String(options.offset));

    const url = `${this.apiUrl}/taxonomies${params.toString() ? `?${params}` : ''}`;
    const response = await fetch(url);

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || error.error || `API error: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Delete a job.
   */
  async deleteJob(jobId: string): Promise<void> {
    const response = await fetch(`${this.apiUrl}/taxonomies/${jobId}`, {
      method: 'DELETE',
    });

    if (!response.ok && response.status !== 204) {
      if (response.status === 404) {
        throw new Error(`Job ${jobId} not found`);
      }
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || error.error || `API error: ${response.status}`);
    }
  }

  /**
   * Check API health.
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.apiUrl}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }
}

// =============================================================================
// Utilities
// =============================================================================

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Create a Delve client instance.
 *
 * @example
 * ```typescript
 * const delve = createClient({ apiUrl: 'https://api.example.com' });
 * ```
 */
export function createClient(options: DelveOptions): Delve {
  return new Delve(options);
}
