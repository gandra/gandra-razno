<script setup lang="ts">
import { ref } from "vue";
import { api } from "../lib/api";

const url = ref("");
const interval = ref(2);
const format = ref("md");
const loading = ref(false);
const result = ref<Record<string, unknown> | null>(null);
const error = ref<string | null>(null);

async function extract() {
  if (!url.value) return;
  loading.value = true;
  error.value = null;
  result.value = null;

  try {
    const { data } = await api.post("/api/v1/youtube/transcript", {
      url: url.value,
      interval_minutes: interval.value,
      output_format: format.value,
    });
    result.value = data;
  } catch (e: unknown) {
    error.value = "Failed to extract transcript.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="max-w-3xl">
    <h2 class="text-xl font-semibold mb-4">YouTube Transcript Extractor</h2>

    <div class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">YouTube URL *</label>
        <input v-model="url" type="url" placeholder="https://youtube.com/watch?v=..." class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" />
      </div>

      <div class="flex gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Interval (min)</label>
          <input v-model.number="interval" type="number" min="1" max="30" class="w-20 px-3 py-2 border rounded-lg" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Format</label>
          <select v-model="format" class="px-3 py-2 border rounded-lg">
            <option value="md">Markdown</option>
            <option value="json">JSON</option>
            <option value="txt">Text</option>
            <option value="html">HTML</option>
          </select>
        </div>
      </div>

      <button @click="extract" :disabled="loading || !url" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition">
        {{ loading ? "Extracting..." : "Extract" }}
      </button>
    </div>

    <div v-if="error" class="mt-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">{{ error }}</div>

    <div v-if="result" class="mt-6 space-y-3">
      <div class="flex items-center gap-4 text-sm text-gray-500">
        <span>{{ (result as Record<string, unknown>).duration_formatted }}</span>
        <span>{{ (result as Record<string, unknown>).segment_count }} segments</span>
        <span>{{ (result as Record<string, unknown>).word_count }} words</span>
      </div>
      <div v-if="(result as Record<string, unknown>).file_path" class="text-sm text-green-600">
        Saved: {{ (result as Record<string, unknown>).file_path }}
      </div>
      <pre class="bg-white border rounded-lg p-4 text-sm overflow-auto max-h-96 whitespace-pre-wrap">{{ (result as Record<string, unknown>).full_text }}</pre>
    </div>
  </div>
</template>
