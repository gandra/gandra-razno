<script setup lang="ts">
import { ref } from "vue";
import { api } from "../lib/api";

const linksText = ref("");
const depth = ref("medium");
const focus = ref("all");
const format = ref("md");
const loading = ref(false);
const result = ref<Record<string, unknown> | null>(null);
const error = ref<string | null>(null);

async function analyze() {
  const links = linksText.value.split("\n").map(l => l.trim()).filter(Boolean);
  if (!links.length) return;
  loading.value = true;
  error.value = null;

  try {
    const { data } = await api.post("/api/v1/research/analyze", {
      links,
      depth: depth.value,
      focus: [focus.value],
      output_format: format.value,
    });
    result.value = data;
  } catch {
    error.value = "Analysis failed.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="max-w-3xl">
    <h2 class="text-xl font-semibold mb-4">RAG Research Analyzer</h2>

    <div class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">URLs (one per line)</label>
        <textarea v-model="linksText" rows="5" placeholder="https://example.com/article1&#10;https://example.com/article2" class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"></textarea>
      </div>

      <div class="flex gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Depth</label>
          <select v-model="depth" class="px-3 py-2 border rounded-lg">
            <option value="shallow">Shallow</option>
            <option value="medium">Medium</option>
            <option value="deep">Deep</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Focus</label>
          <select v-model="focus" class="px-3 py-2 border rounded-lg">
            <option value="all">All</option>
            <option value="credibility">Credibility</option>
            <option value="narrative">Narrative</option>
            <option value="summary">Summary</option>
            <option value="fact_check">Fact Check</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Format</label>
          <select v-model="format" class="px-3 py-2 border rounded-lg">
            <option value="md">Markdown</option>
            <option value="json">JSON</option>
            <option value="html">HTML</option>
          </select>
        </div>
      </div>

      <button @click="analyze" :disabled="loading" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition">
        {{ loading ? "Analyzing..." : "Analyze" }}
      </button>
    </div>

    <div v-if="error" class="mt-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">{{ error }}</div>

    <div v-if="result" class="mt-6 space-y-4">
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 class="font-semibold text-blue-800 mb-2">Executive Summary</h3>
        <p class="text-sm text-blue-700">{{ (result as Record<string, unknown>).executive_summary }}</p>
      </div>
      <div class="text-sm text-gray-500">
        Sources: {{ (result as Record<string, unknown>).sources_analyzed }} |
        Confidence: {{ Math.round(((result as Record<string, unknown>).confidence_score as number) * 100) }}%
      </div>
    </div>
  </div>
</template>
