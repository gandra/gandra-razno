<script setup lang="ts">
import { ref } from "vue";
import { api } from "../lib/api";

const imagePath = ref("");
const mode = ref("ocr");
const fontColor = ref("auto");
const minConfidence = ref(0.5);
const loading = ref(false);
const result = ref<Record<string, unknown> | null>(null);
const error = ref<string | null>(null);

async function extract() {
  if (!imagePath.value) return;
  loading.value = true;
  error.value = null;
  try {
    const { data } = await api.post("/api/v1/imageops/text-extract", {
      image_path: imagePath.value,
      mode: mode.value,
      font_color: fontColor.value,
      min_confidence: minConfidence.value,
    });
    result.value = data;
  } catch {
    error.value = "Extraction failed.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="max-w-3xl">
    <h2 class="text-xl font-semibold mb-4">Image Text Extractor</h2>
    <div class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Image path or URL *</label>
        <input v-model="imagePath" placeholder="./screenshot.jpg or https://..." class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" />
      </div>
      <div class="flex gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Mode</label>
          <select v-model="mode" class="px-3 py-2 border rounded-lg">
            <option value="ocr">OCR</option>
            <option value="mask">Mask</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Font color</label>
          <select v-model="fontColor" class="px-3 py-2 border rounded-lg">
            <option value="auto">Auto</option>
            <option value="black">Black</option>
            <option value="white">White</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Min confidence</label>
          <input v-model.number="minConfidence" type="number" min="0" max="1" step="0.1" class="w-20 px-3 py-2 border rounded-lg" />
        </div>
      </div>
      <button @click="extract" :disabled="loading || !imagePath" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition">
        {{ loading ? "Processing..." : "Extract" }}
      </button>
    </div>
    <div v-if="error" class="mt-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">{{ error }}</div>
    <div v-if="result" class="mt-6 text-sm text-gray-600">
      <p>Regions: {{ (result as Record<string, unknown>).regions_included }}/{{ (result as Record<string, unknown>).regions_detected }} | {{ (result as Record<string, unknown>).processing_time_ms }}ms</p>
      <p v-if="(result as Record<string, unknown>).extracted_text" class="mt-2 bg-white border rounded-lg p-3">{{ (result as Record<string, unknown>).extracted_text }}</p>
    </div>
  </div>
</template>
