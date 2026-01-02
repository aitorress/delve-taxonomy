/**
 * Delve - AI-powered taxonomy generation for your data.
 *
 * @packageDocumentation
 *
 * @example
 * ```typescript
 * import { Delve } from '@delve/taxonomy';
 *
 * // Create client
 * const delve = new Delve({
 *   maxNumClusters: 5,
 *   useCase: 'Categorize customer feedback',
 * });
 *
 * // Generate taxonomy
 * const result = await delve.run([
 *   'The app crashes when I click submit',
 *   'Please add dark mode support',
 *   'How do I reset my password?',
 * ]);
 *
 * // Access results
 * console.log('Categories:', result.taxonomy);
 * console.log('Labeled docs:', result.labeledDocuments);
 * ```
 */

// Main client
export { Delve, generateTaxonomy } from "./client.js";

// Types
export type {
  Doc,
  TaxonomyCategory,
  DelveResult,
  DelveConfig,
  DelveMetadata,
  ClassifierMetrics,
  PredefinedCategory,
  RunOptions,
} from "./types.js";
