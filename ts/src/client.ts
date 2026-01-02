/**
 * Main Delve client for taxonomy generation.
 */

import { StateGraph, START, END } from "@langchain/langgraph";
import type {
  Doc,
  DelveConfig,
  DelveResult,
  GraphState,
  RunOptions,
  TaxonomyCategory,
  PredefinedCategory,
} from "./types.js";
import {
  loadData,
  summarize,
  getMinibatches,
  generateTaxonomy,
  updateTaxonomy,
  reviewTaxonomy,
  labelDocuments,
  shouldReview,
  shouldDiscoverTaxonomy,
} from "./nodes.js";
import { countCategories } from "./utils.js";

/**
 * Default configuration values.
 */
const DEFAULT_CONFIG: Required<
  Omit<DelveConfig, "anthropicApiKey" | "openaiApiKey" | "useCase">
> = {
  model: "claude-sonnet-4-5-20250929",
  fastLlm: "claude-haiku-4-5-20251001",
  sampleSize: 100,
  batchSize: 200,
  maxNumClusters: 5,
  embeddingModel: "text-embedding-3-large",
  classifierConfidenceThreshold: 0.0,
};

/**
 * Delve - AI-powered taxonomy generation.
 *
 * @example
 * ```typescript
 * import { Delve } from '@delve/taxonomy';
 *
 * const delve = new Delve({ maxNumClusters: 5 });
 *
 * const result = await delve.run([
 *   { id: '1', content: 'Fix the login button' },
 *   { id: '2', content: 'Add dark mode support' },
 * ]);
 *
 * console.log(result.taxonomy);
 * ```
 */
export class Delve {
  private config: DelveConfig;

  /**
   * Create a new Delve instance.
   *
   * @param config - Configuration options
   */
  constructor(config: DelveConfig = {}) {
    this.config = {
      ...DEFAULT_CONFIG,
      ...config,
    };
  }

  /**
   * Run taxonomy generation on documents.
   *
   * @param documents - Documents to process (strings or Doc objects)
   * @param options - Run options
   * @returns Taxonomy and labeled documents
   *
   * @example
   * ```typescript
   * // With strings
   * const result = await delve.run([
   *   'Fix authentication bug',
   *   'Add new feature',
   * ]);
   *
   * // With Doc objects
   * const result = await delve.run([
   *   { id: '1', content: 'Fix bug' },
   *   { id: '2', content: 'Add feature' },
   * ]);
   *
   * // With predefined taxonomy
   * const result = await delve.run(documents, {
   *   predefinedTaxonomy: [
   *     { id: '1', name: 'Bug', description: 'Bug reports' },
   *     { id: '2', name: 'Feature', description: 'Feature requests' },
   *   ],
   * });
   * ```
   */
  async run(
    documents: (string | Doc)[],
    options: RunOptions = {}
  ): Promise<DelveResult> {
    const startTime = Date.now();

    // Normalize documents to Doc format
    const docs: Doc[] = documents.map((doc, index) => {
      if (typeof doc === "string") {
        return { id: String(index + 1), content: doc };
      }
      return { ...doc, id: doc.id || String(index + 1) };
    });

    // Build initial state
    const initialState: GraphState = {
      allDocuments: docs,
      documents: [],
      minibatches: [],
      clusters: options.predefinedTaxonomy
        ? [this.normalizePredefinedTaxonomy(options.predefinedTaxonomy)]
        : [],
      useCase:
        options.useCase ||
        this.config.useCase ||
        "Generate taxonomy for categorizing document content",
      status: [],
      llmLabeledCount: 0,
      classifierLabeledCount: 0,
      skippedDocumentCount: 0,
      warnings: [],
    };

    // Build and run graph
    const graph = this.buildGraph();
    const result = await graph.invoke(initialState, {
      configurable: this.config,
    });

    const endTime = Date.now();
    const durationSeconds = (endTime - startTime) / 1000;

    // Build result
    return this.buildResult(result, durationSeconds);
  }

  /**
   * Build the LangGraph workflow.
   */
  private buildGraph() {
    const builder = new StateGraph<GraphState>({
      channels: {
        allDocuments: { default: () => [] },
        documents: { default: () => [] },
        minibatches: { default: () => [] },
        clusters: {
          default: () => [],
          reducer: (current, update) => [...current, ...update],
        },
        useCase: { default: () => "" },
        status: {
          default: () => [],
          reducer: (current, update) => [...current, ...update],
        },
        classifierMetrics: { default: () => undefined },
        llmLabeledCount: { default: () => 0 },
        classifierLabeledCount: { default: () => 0 },
        skippedDocumentCount: { default: () => 0 },
        warnings: {
          default: () => [],
          reducer: (current, update) => [...current, ...update],
        },
      },
    });

    // Add nodes
    builder.addNode("load_data", loadData);
    builder.addNode("summarize", summarize);
    builder.addNode("get_minibatches", getMinibatches);
    builder.addNode("generate_taxonomy", generateTaxonomy);
    builder.addNode("update_taxonomy", updateTaxonomy);
    builder.addNode("review_taxonomy", reviewTaxonomy);
    builder.addNode("label_documents", labelDocuments);

    // Add edges
    builder.addEdge(START, "load_data");

    // Conditional: skip discovery if predefined taxonomy
    builder.addConditionalEdges("load_data", shouldDiscoverTaxonomy, {
      summarize: "summarize",
      label_documents: "label_documents",
    });

    // Discovery flow
    builder.addEdge("summarize", "get_minibatches");
    builder.addEdge("get_minibatches", "generate_taxonomy");
    builder.addEdge("generate_taxonomy", "update_taxonomy");

    // Update loop
    builder.addConditionalEdges("update_taxonomy", shouldReview, {
      update_taxonomy: "update_taxonomy",
      review_taxonomy: "review_taxonomy",
    });

    // Final steps
    builder.addEdge("review_taxonomy", "label_documents");
    builder.addEdge("label_documents", END);

    return builder.compile();
  }

  /**
   * Normalize predefined taxonomy to TaxonomyCategory format.
   */
  private normalizePredefinedTaxonomy(
    taxonomy: PredefinedCategory[]
  ): TaxonomyCategory[] {
    return taxonomy.map((cat) => ({
      id: cat.id,
      name: cat.name,
      description: cat.description,
    }));
  }

  /**
   * Build the final result from graph state.
   */
  private buildResult(state: GraphState, durationSeconds: number): DelveResult {
    const taxonomy = state.clusters[state.clusters.length - 1] || [];
    const labeledDocuments = state.documents;
    const categoryCounts = countCategories(labeledDocuments);

    return {
      taxonomy,
      labeledDocuments,
      metadata: {
        numDocuments: state.allDocuments.length,
        numCategories: taxonomy.length,
        sampleSize: this.config.sampleSize ?? DEFAULT_CONFIG.sampleSize,
        batchSize: this.config.batchSize ?? DEFAULT_CONFIG.batchSize,
        model: this.config.model ?? DEFAULT_CONFIG.model,
        fastLlm: this.config.fastLlm ?? DEFAULT_CONFIG.fastLlm,
        runDurationSeconds: Math.round(durationSeconds * 100) / 100,
        categoryCounts,
        llmLabeledCount: state.llmLabeledCount,
        classifierLabeledCount: state.classifierLabeledCount,
        skippedDocumentCount: state.skippedDocumentCount,
        classifierMetrics: state.classifierMetrics,
        warnings: state.warnings,
        statusLog: state.status,
      },
    };
  }
}

/**
 * Convenience function for one-off taxonomy generation.
 *
 * @example
 * ```typescript
 * import { generateTaxonomy } from '@delve/taxonomy';
 *
 * const result = await generateTaxonomy([
 *   'Fix login bug',
 *   'Add dark mode',
 * ], {
 *   useCase: 'Categorize software issues',
 *   maxNumClusters: 5,
 * });
 * ```
 */
export async function generateTaxonomy(
  documents: (string | Doc)[],
  config: DelveConfig & RunOptions = {}
): Promise<DelveResult> {
  const { useCase, predefinedTaxonomy, ...delveConfig } = config;
  const delve = new Delve(delveConfig);
  return delve.run(documents, { useCase, predefinedTaxonomy });
}
