<script setup lang="ts">
import { ref } from "vue";
import { api } from "../lib/api";

const messages = ref<{ role: string; content: string }[]>([]);
const input = ref("");
const loading = ref(false);

async function send() {
  if (!input.value.trim()) return;
  const userMsg = input.value;
  messages.value.push({ role: "user", content: userMsg });
  input.value = "";
  loading.value = true;

  try {
    const { data } = await api.post("/api/v1/chat", { message: userMsg });
    messages.value.push({ role: "assistant", content: data.response || data.content || "..." });
  } catch {
    messages.value.push({ role: "assistant", content: "Error: Could not get response." });
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Messages -->
    <div class="flex-1 overflow-auto space-y-4 pb-4">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="max-w-2xl"
        :class="msg.role === 'user' ? 'ml-auto' : ''"
      >
        <div
          class="px-4 py-3 rounded-lg text-sm"
          :class="msg.role === 'user'
            ? 'bg-blue-600 text-white'
            : 'bg-white border border-gray-200 text-gray-800'"
        >
          {{ msg.content }}
        </div>
      </div>
      <div v-if="loading" class="text-gray-400 text-sm">Thinking...</div>
    </div>

    <!-- Input -->
    <form @submit.prevent="send" class="flex gap-2 pt-4 border-t border-gray-200">
      <input
        v-model="input"
        placeholder="Ask anything..."
        class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
      />
      <button
        type="submit"
        :disabled="loading"
        class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
      >
        Send
      </button>
    </form>
  </div>
</template>
