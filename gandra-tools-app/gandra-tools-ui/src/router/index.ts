import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/chat" },
    { path: "/chat", component: () => import("../pages/ChatPage.vue"), meta: { title: "Chat" } },
    { path: "/youtube", component: () => import("../pages/YoutubePage.vue"), meta: { title: "YouTube" } },
    { path: "/research", component: () => import("../pages/ResearchPage.vue"), meta: { title: "Research" } },
    { path: "/imageops", component: () => import("../pages/ImageOpsPage.vue"), meta: { title: "Image Ops" } },
    { path: "/fileops", component: () => import("../pages/FileOpsPage.vue"), meta: { title: "File Ops" } },
    { path: "/devtools", component: () => import("../pages/DevToolsPage.vue"), meta: { title: "DevTools" } },
    { path: "/settings", component: () => import("../pages/SettingsPage.vue"), meta: { title: "Settings" } },
  ],
});

export default router;
