/**
 * Utility functions for Delve.
 */

import { ChatAnthropic } from "@langchain/anthropic";
import type { TaxonomyCategory, Doc } from "./types.js";

/**
 * Load a chat model by name.
 */
export function loadChatModel(
  modelName: string,
  apiKey?: string
): ChatAnthropic {
  // Normalize model name (remove provider prefix if present)
  const normalizedName = modelName.replace(/^anthropic\//, "");

  return new ChatAnthropic({
    model: normalizedName,
    anthropicApiKey: apiKey,
  });
}

/**
 * Parse taxonomy categories from XML string.
 */
export function parseTaxonomy(xmlString: string): TaxonomyCategory[] {
  const clusters: TaxonomyCategory[] = [];

  // Extract cluster_table content
  const tableMatch = xmlString.match(
    /<cluster_table>([\s\S]*?)<\/cluster_table>/
  );
  const content = tableMatch ? tableMatch[1] : xmlString;

  // Extract individual clusters
  const clusterRegex = /<cluster>([\s\S]*?)<\/cluster>/g;
  let match;

  while ((match = clusterRegex.exec(content)) !== null) {
    const clusterXml = match[1];

    const idMatch = clusterXml.match(/<id>\s*(\d+)\s*<\/id>/);
    const nameMatch = clusterXml.match(/<name>\s*([\s\S]*?)\s*<\/name>/);
    const descMatch = clusterXml.match(
      /<description>\s*([\s\S]*?)\s*<\/description>/
    );

    if (idMatch && nameMatch) {
      clusters.push({
        id: idMatch[1].trim(),
        name: nameMatch[1].trim(),
        description: descMatch ? descMatch[1].trim() : "",
      });
    }
  }

  return clusters;
}

/**
 * Parse summary from XML output.
 */
export function parseSummary(
  xmlString: string
): { summary: string; explanation: string } {
  const summaryMatch = xmlString.match(/<summary>([\s\S]*?)<\/summary>/);
  const explanationMatch = xmlString.match(
    /<explanation>([\s\S]*?)<\/explanation>/
  );

  return {
    summary: summaryMatch ? summaryMatch[1].trim() : "",
    explanation: explanationMatch ? explanationMatch[1].trim() : "",
  };
}

/**
 * Parse category ID from labeler output.
 */
export function parseCategoryId(output: string): string | null {
  const match = output.match(/<category_id>\s*(\d+)\s*<\/category_id>/);
  return match ? match[1] : null;
}

/**
 * Get category name by ID from taxonomy.
 */
export function getCategoryNameById(
  categoryId: string,
  taxonomy: TaxonomyCategory[]
): string {
  const category = taxonomy.find((c) => c.id === categoryId);
  if (!category) {
    throw new Error(
      `Category ID '${categoryId}' not found in taxonomy. ` +
        `Available IDs: ${taxonomy.map((c) => c.id).join(", ")}`
    );
  }
  return category.name;
}

/**
 * Format taxonomy as XML for the labeler prompt.
 */
export function formatTaxonomyAsXml(taxonomy: TaxonomyCategory[]): string {
  let xml = "<cluster_table>\n";

  for (const cluster of taxonomy) {
    xml += "  <cluster>\n";
    xml += `    <id>${cluster.id}</id>\n`;
    xml += `    <name>${cluster.name}</name>\n`;
    xml += `    <description>${cluster.description}</description>\n`;
    xml += "  </cluster>\n";
  }

  xml += "</cluster_table>";
  return xml;
}

/**
 * Format documents as XML for taxonomy generation.
 */
export function formatDocsAsXml(docs: Doc[]): string {
  let xml = "";

  for (const doc of docs) {
    xml += `<conversation>\n`;
    xml += `  <id>${doc.id}</id>\n`;
    xml += `  <text>${doc.summary || doc.content}</text>\n`;
    xml += `</conversation>\n`;
  }

  return xml;
}

/**
 * Sample documents randomly.
 */
export function sampleDocuments(docs: Doc[], sampleSize: number): Doc[] {
  if (sampleSize <= 0 || sampleSize >= docs.length) {
    return [...docs];
  }

  // Fisher-Yates shuffle and take first n
  const shuffled = [...docs];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }

  return shuffled.slice(0, sampleSize);
}

/**
 * Generate minibatches from document indices.
 */
export function generateMinibatches(
  docCount: number,
  batchSize: number
): number[][] {
  const batches: number[][] = [];
  const indices = Array.from({ length: docCount }, (_, i) => i);

  for (let i = 0; i < indices.length; i += batchSize) {
    batches.push(indices.slice(i, i + batchSize));
  }

  return batches;
}

/**
 * Count documents per category.
 */
export function countCategories(docs: Doc[]): Record<string, number> {
  const counts: Record<string, number> = {};

  for (const doc of docs) {
    if (doc.category) {
      counts[doc.category] = (counts[doc.category] || 0) + 1;
    }
  }

  return counts;
}
