<template>
  <div class="flex h-screen w-screen bg-[#0c1222]">
    <MobileSidebar />
    <div
      class="flex h-full min-w-0 flex-1 flex-col overflow-auto rounded-tl-2xl bg-[#f1f5f9]"
    >
      <MobileAppHeader />
      <slot />
    </div>
    <GlobalModals />
  </div>
</template>
<script setup>
import MobileSidebar from '@/components/Mobile/MobileSidebar.vue'
import MobileAppHeader from '@/components/Mobile/MobileAppHeader.vue'
import GlobalModals from '@/components/Modals/GlobalModals.vue'
</script>
