/**
 * LangGraph nodes for taxonomy generation workflow.
 */

import { StringOutputParser } from "@langchain/core/output_parsers";
import type { RunnableConfig } from "@langchain/core/runnables";
import type { GraphState, TaxonomyCategory, Doc, DelveConfig } from "./types.js";
import { LABELER_PROMPT, TAXONOMY_GENERATION_PROMPT, SUMMARY_PROMPT } from "./prompts.js";
import {
  loadChatModel,
  parseTaxonomy,
  parseSummary,
  parseCategoryId,
  getCategoryNameById,
  formatTaxonomyAsXml,
  formatDocsAsXml,
  sampleDocuments,
  generateMinibatches,
} from "./utils.js";

/**
 * Get config from runnable config.
 */
function getConfig(config?: RunnableConfig): DelveConfig {
  return (config?.configurable as DelveConfig) || {};
}

/**
 * Load and sample documents.
 */
export async function loadData(
  state: GraphState,
  config?: RunnableConfig
): Promise<Partial<GraphState>> {
  const cfg = getConfig(config);
  const sampleSize = cfg.sampleSize ?? 100;

  // Sample documents if needed
  const documents = sampleDocuments(state.allDocuments, sampleSize);

  return {
    documents,
    useCase: cfg.useCase || "Generate taxonomy for categorizing document content",
    status: [`Loaded ${state.allDocuments.length} documents, sampled ${documents.length}`],
  };
}

/**
 * Generate summaries for documents.
 */
export async function summarize(
  state: GraphState,
  config?: RunnableConfig
): Promise<Partial<GraphState>> {
  const cfg = getConfig(config);
  const model = loadChatModel(
    cfg.fastLlm || "claude-haiku-4-5-20251001",
    cfg.anthropicApiKey
  );

  const prompt = SUMMARY_PROMPT.partial({
    summary_length: "20",
  });

  const chain = prompt.pipe(model).pipe(new StringOutputParser());

  const summarizedDocs: Doc[] = [];

  for (const doc of state.documents) {
    const result = await chain.invoke({ content: doc.content });
    const parsed = parseSummary(result);

    summarizedDocs.push({
      ...doc,
      summary: parsed.summary,
      explanation: parsed.explanation,
    });
  }

  return {
    documents: summarizedDocs,
    status: [`Summarized ${summarizedDocs.length} documents`],
  };
}

/**
 * Generate minibatches from documents.
 */
export async function getMinibatches(
  state: GraphState,
  config?: RunnableConfig
): Promise<Partial<GraphState>> {
  const cfg = getConfig(config);
  const batchSize = cfg.batchSize ?? 200;

  const minibatches = generateMinibatches(state.documents.length, batchSize);

  return {
    minibatches,
    status: [`Generated ${minibatches.length} minibatches`],
  };
}

/**
 * Generate initial taxonomy from first batch.
 */
export async function generateTaxonomy(
  state: GraphState,
  config?: RunnableConfig
): Promise<Partial<GraphState>> {
  const cfg = getConfig(config);
  const model = loadChatModel(
    cfg.model || "claude-sonnet-4-5-20250929",
    cfg.anthropicApiKey
  );

  const maxClusters = cfg.maxNumClusters ?? 5;

  const prompt = TAXONOMY_GENERATION_PROMPT.partial({
    use_case: state.useCase,
    feedback: "No previous feedback provided.",
    cluster_name_length: "5",
    cluster_description_length: "20",
    max_num_clusters: String(maxClusters),
    explanation_length: "100",
  });

  const chain = prompt.pipe(model).pipe(new StringOutputParser());

  // Get first batch documents
  const firstBatch = state.minibatches[0];
  const batchDocs = firstBatch.map((i) => state.documents[i]);
  const dataXml = formatDocsAsXml(batchDocs);

  const result = await chain.invoke({ data_xml: dataXml });
  const taxonomy = parseTaxonomy(result);

  return {
    clusters: [taxonomy],
    status: [`Generated initial taxonomy with ${taxonomy.length} categories`],
  };
}

/**
 * Update taxonomy with next batch.
 */
export async function updateTaxonomy(
  state: GraphState,
  config?: RunnableConfig
): Promise<Partial<GraphState>> {
  const cfg = getConfig(config);
  const model = loadChatModel(
    cfg.model || "claude-sonnet-4-5-20250929",
    cfg.anthropicApiKey
  );

  const maxClusters = cfg.maxNumClusters ?? 5;
  const currentClusters = state.clusters[state.clusters.length - 1];
  const currentBatchIndex = state.clusters.length;

  // Check if we have more batches
  if (currentBatchIndex >= state.minibatches.length) {
    return {
      status: ["No more batches to process"],
    };
  }

  // Format existing taxonomy as feedback
  const existingTaxonomyXml = formatTaxonomyAsXml(currentClusters);
  const feedback = `Please consider the existing taxonomy when refining:\n${existingTaxonomyXml}`;

  const prompt = TAXONOMY_GENERATION_PROMPT.partial({
    use_case: state.useCase,
    feedback,
    cluster_name_length: "5",
    cluster_description_length: "20",
    max_num_clusters: String(maxClusters),
    explanation_length: "100",
  });

  const chain = prompt.pipe(model).pipe(new StringOutputParser());

  // Get batch documents
  const batchIndices = state.minibatches[currentBatchIndex];
  const batchDocs = batchIndices.map((i) => state.documents[i]);
  const dataXml = formatDocsAsXml(batchDocs);

  const result = await chain.invoke({ data_xml: dataXml });
  const taxonomy = parseTaxonomy(result);

  return {
    clusters: [taxonomy],
    status: [`Updated taxonomy (batch ${currentBatchIndex + 1}/${state.minibatches.length})`],
  };
}

/**
 * Review and finalize taxonomy.
 */
export async function reviewTaxonomy(
  state: GraphState,
  config?: RunnableConfig
): Promise<Partial<GraphState>> {
  // For now, just use the latest taxonomy as final
  const finalTaxonomy = state.clusters[state.clusters.length - 1];

  return {
    status: [`Finalized taxonomy with ${finalTaxonomy.length} categories`],
  };
}

/**
 * Label all documents with the taxonomy.
 */
export async function labelDocuments(
  state: GraphState,
  config?: RunnableConfig
): Promise<Partial<GraphState>> {
  const cfg = getConfig(config);
  const model = loadChatModel(
    cfg.fastLlm || "claude-haiku-4-5-20251001",
    cfg.anthropicApiKey
  );

  const taxonomy = state.clusters[state.clusters.length - 1];
  const taxonomyXml = formatTaxonomyAsXml(taxonomy);

  const chain = LABELER_PROMPT.pipe(model).pipe(new StringOutputParser());

  const labeledDocs: Doc[] = [];
  const warnings: string[] = [];
  let skippedCount = 0;

  // Label all documents (not just sampled)
  for (const doc of state.allDocuments) {
    const result = await chain.invoke({
      content: doc.content,
      taxonomy: taxonomyXml,
    });

    const categoryId = parseCategoryId(result);

    let categoryName: string;
    if (!categoryId) {
      warnings.push(`No category ID for doc ${doc.id}, using 'Other'`);
      categoryName = "Other";
      skippedCount++;
    } else {
      try {
        categoryName = getCategoryNameById(categoryId, taxonomy);
      } catch {
        warnings.push(`Invalid category ID ${categoryId} for doc ${doc.id}, using 'Other'`);
        categoryName = "Other";
        skippedCount++;
      }
    }

    labeledDocs.push({
      ...doc,
      category: categoryName,
    });
  }

  return {
    documents: labeledDocs,
    llmLabeledCount: labeledDocs.length,
    classifierLabeledCount: 0,
    skippedDocumentCount: skippedCount,
    warnings: [...state.warnings, ...warnings],
    status: [`Labeled ${labeledDocs.length} documents`],
  };
}

/**
 * Routing function: should we continue updating or review?
 */
export function shouldReview(state: GraphState): "update_taxonomy" | "review_taxonomy" {
  const processedBatches = state.clusters.length;
  const totalBatches = state.minibatches.length;

  if (processedBatches >= totalBatches) {
    return "review_taxonomy";
  }

  return "update_taxonomy";
}

/**
 * Routing function: should we discover taxonomy or skip to labeling?
 */
export function shouldDiscoverTaxonomy(
  state: GraphState
): "summarize" | "label_documents" {
  // If we have pre-defined taxonomy in clusters, skip discovery
  if (state.clusters.length > 0) {
    return "label_documents";
  }

  return "summarize";
}
