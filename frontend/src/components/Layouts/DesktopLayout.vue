<template>
  <div class="flex h-screen w-screen bg-[#0c1222]">
    <div
      class="nexus-sidebar-shell h-full shrink-0 border-r border-slate-700/60 bg-[#0f172a]"
    >
      <AppSidebar />
    </div>
    <div
      class="flex min-h-0 min-w-0 flex-1 flex-col overflow-auto rounded-tl-2xl bg-[#f1f5f9]"
    >
      <AppHeader />
      <slot />
    </div>
    <GlobalModals />
  </div>
</template>
<script setup>
import AppSidebar from '@/components/Layouts/AppSidebar.vue'
import AppHeader from '@/components/Layouts/AppHeader.vue'
import GlobalModals from '@/components/Modals/GlobalModals.vue'
</script>
