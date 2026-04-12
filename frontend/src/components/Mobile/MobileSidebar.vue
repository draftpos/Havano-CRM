<template>
  <TransitionRoot :show="sidebarOpened">
    <Dialog as="div" class="fixed inset-0" @close="sidebarOpened = false">
      <TransitionChild
        as="template"
        enter="transition ease-in-out duration-200 transform"
        enter-from="-translate-x-full"
        enter-to="translate-x-0"
        leave="transition ease-in-out duration-200 transform"
        leave-from="translate-x-0"
        leave-to="-translate-x-full"
      >
        <div
          class="nexus-sidebar relative z-10 flex h-full w-[260px] flex-col justify-between border-r border-slate-700/60 bg-[#0f172a] text-slate-100 transition-all duration-300 ease-in-out"
        >
          <div>
            <UserDropdown class="p-2" :isCollapsed="!sidebarOpened" />
          </div>
          <div class="flex-1 overflow-y-auto">
            <div class="mb-3 flex flex-col">
              <SidebarLink
                id="notifications-btn"
                nexus
                :label="__('Notifications')"
                :icon="NotificationsIcon"
                :to="{ name: 'Notifications' }"
                class="relative mx-2 my-0.5"
              >
                <template #right>
                  <Badge
                    v-if="unreadNotificationsCount"
                    :label="unreadNotificationsCount"
                    variant="solid"
                    theme="red"
                    class="!min-w-[1.25rem] shrink-0 border-0 !px-1.5 !text-[11px] font-semibold"
                  />
                </template>
              </SidebarLink>
            </div>
            <div v-for="view in allViews" :key="view.name">
              <CollapsibleSection
                :label="view.name"
                :hideLabel="view.hideLabel"
                :opened="view.opened"
              >
                <template #header="{ opened, hide, toggle }">
                  <div
                    v-if="!hide"
                    class="nexus-sidebar-section mx-2 mt-3 flex min-h-7 w-auto cursor-pointer items-center gap-1.5 rounded-md px-3 py-2 text-xs font-semibold uppercase tracking-wide !text-slate-200 opacity-100 transition-colors duration-200 ease-in-out hover:bg-white/10"
                    @click="toggle()"
                  >
                    <FeatherIcon
                      name="chevron-right"
                      class="h-4 shrink-0 !text-slate-300 transition-transform duration-300 ease-in-out"
                      :class="{ 'rotate-90': opened }"
                    />
                    <span class="!text-slate-100">{{ __(view.name) }}</span>
                  </div>
                </template>
                <nav class="flex flex-col">
                  <SidebarLink
                    v-for="link in view.views"
                    :key="link.label"
                    nexus
                    :icon="link.icon"
                    :label="__(link.label)"
                    :to="link.to"
                    class="mx-2 my-0.5"
                  />
                </nav>
              </CollapsibleSection>
            </div>
          </div>
        </div>
      </TransitionChild>
      <TransitionChild
        as="template"
        enter="transition-opacity ease-linear duration-200"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="transition-opacity ease-linear duration-200"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <DialogOverlay class="fixed inset-0 bg-surface-gray-5 bg-opacity-50" />
      </TransitionChild>
    </Dialog>
  </TransitionRoot>
</template>
<script setup>
import {
  TransitionRoot,
  TransitionChild,
  Dialog,
  DialogOverlay,
} from '@headlessui/vue'
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import UserDropdown from '@/components/UserDropdown.vue'
import NotificationsIcon from '@/components/Icons/NotificationsIcon.vue'
import SidebarLink from '@/components/SidebarLink.vue'
import { unreadNotificationsCount } from '@/stores/notifications'
import { FeatherIcon } from 'frappe-ui'
import { provide } from 'vue'
import { useNexusAllViews } from '@/composables/nexusNav'
import { mobileSidebarOpened as sidebarOpened } from '@/composables/settings'

const allViews = useNexusAllViews()
provide('nexusSidebar', true)
</script>
