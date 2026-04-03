import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { api } from "../lib/api";

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string | null>(localStorage.getItem("gandra_token"));
  const userEmail = ref<string | null>(localStorage.getItem("gandra_user"));
  const error = ref<string | null>(null);

  const isAuthenticated = computed(() => !!token.value);

  async function login(email: string, password: string) {
    error.value = null;
    try {
      const { data } = await api.post("/api/v1/auth/login", { email, password });
      token.value = data.access_token;
      userEmail.value = email;
      localStorage.setItem("gandra_token", data.access_token);
      localStorage.setItem("gandra_user", email);
    } catch (e: unknown) {
      error.value = "Invalid credentials";
    }
  }

  function logout() {
    token.value = null;
    userEmail.value = null;
    localStorage.removeItem("gandra_token");
    localStorage.removeItem("gandra_user");
  }

  return { token, userEmail, error, isAuthenticated, login, logout };
});
