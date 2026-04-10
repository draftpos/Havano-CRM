<template>
  <button
    type="button"
    class="flex h-7.5 cursor-pointer items-center rounded duration-300 ease-in-out focus:outline-none focus:transition-none focus-visible:rounded"
    :class="[
      isNexus
        ? isActive
          ? 'nexus-rail nexus-rail-active bg-sky-500/40 !text-white shadow-none ring-1 ring-white/10 [&_svg]:!text-white'
          : nexusTone === 'danger'
            ? 'nexus-rail nexus-rail-danger !text-red-300 hover:bg-red-950/55 [&_svg]:!text-red-300'
            : 'nexus-rail !text-slate-100 hover:bg-white/12 [&_svg]:!text-slate-100'
        : isActive
          ? 'bg-surface-selected text-ink-gray-8 shadow-sm'
          : 'text-ink-gray-8 hover:bg-surface-gray-2',
      isNexus
        ? 'focus-visible:ring-2 focus-visible:ring-sky-400 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0f172a]'
        : 'focus-visible:ring-2 focus-visible:ring-outline-gray-3',
    ]"
    @click="handleClick"
  >
    <div
      class="flex w-full items-center justify-between duration-300 ease-in-out"
      :class="isCollapsed ? 'ml-[3px] p-1' : 'px-2 py-[7px]'"
    >
      <div class="flex items-center truncate">
        <Tooltip :text="label" placement="right" :disabled="!isCollapsed">
          <slot name="icon">
            <Icon
              :icon="icon"
              class="flex size-4 items-center shrink-0"
              :class="isNexus ? '!text-slate-100' : 'text-ink-gray-8'"
            />
          </slot>
        </Tooltip>
        <Tooltip
          :text="label"
          placement="right"
          :disabled="isCollapsed"
          :hoverDelay="1.5"
        >
          <span
            class="flex-1 flex-shrink-0 truncate text-sm duration-300 ease-in-out"
            :class="[
              isCollapsed
                ? 'ml-0 w-0 overflow-hidden opacity-0'
                : 'ml-2 w-auto opacity-100',
              isNexus && isActive ? '!text-white' : '',
              isNexus && !isActive ? '!text-slate-100' : '',
            ]"
          >
            {{ label }}
          </span>
        </Tooltip>
      </div>
      <slot name="right" />
    </div>
  </button>
</template>

<script setup>
import Icon from '@/components/Icon.vue'
import { Tooltip } from 'frappe-ui'
import { computed, inject } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { isMobileView, mobileSidebarOpened } from '@/composables/settings'

const router = useRouter()
const route = useRoute()

const props = defineProps({
  icon: { type: [Object, String, Function], default: null },
  label: { type: String, default: '' },
  to: { type: [Object, String], default: null },
  isCollapsed: { type: Boolean, default: false },
  /** Dark Nexus rail; omit to use inject('nexusSidebar'), or pass false (e.g. Settings modal). */
  nexus: { type: Boolean, default: undefined },
  /** When nexus, use destructive styling (e.g. Clear demo). */
  nexusTone: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'danger'].includes(v),
  },
})

const nexusInjected = inject('nexusSidebar', false)
const isNexus = computed(() =>
  props.nexus !== undefined ? props.nexus : nexusInjected,
)

function routeTargetName(to) {
  if (!to) return null
  if (typeof to === 'string') return to
  return to.name ?? null
}

function handleClick() {
  if (!props.to) return
  if (typeof props.to === 'object') {
    router.push(props.to)
  } else {
    router.push({ name: props.to })
  }
  if (isMobileView.value) {
    mobileSidebarOpened.value = false
  }
}

const isActive = computed(() => {
  if (route.query.view) {
    return route.query.view == props.to?.query?.view
  }
  const target = routeTargetName(props.to)
  return target != null && route.name === target
})
</script>
