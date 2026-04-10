<template>
  <ListView
    :columns="columns"
    :rows="rows"
    :options="{
      onRowClick: (row) => emit('showTask', row.name),
      selectable: options.selectable,
      showTooltip: options.showTooltip,
      resizeColumn: options.resizeColumn,
    }"
    row-key="name"
    @update:selections="(selections) => emit('selectionsChanged', selections)"
  >
    <ListHeader
      class="mx-3 sm:mx-5"
      @columnWidthUpdated="emit('columnWidthUpdated')"
    >
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
        @columnWidthUpdated="emit('columnWidthUpdated', column)"
      >
        <Button
          v-if="column.key == '_liked_by'"
          variant="ghosted"
          class="!h-4"
          :class="isLikeFilterApplied ? 'fill-red-500' : 'fill-white'"
          @click="() => emit('applyLikeFilter')"
        >
          <HeartIcon class="h-4 w-4" />
        </Button>
      </ListHeaderItem>
    </ListHeader>
    <ListRows
      v-slot="{ idx, column, item, row }"
      class="mx-3 sm:mx-5"
      :rows="rows"
      doctype="ToDo"
    >
      <div
        v-if="(column.key === 'date' || column.key === 'due_date') && item"
        class="flex items-center gap-2 truncate text-base"
      >
        <Tooltip :text="dueTooltipText(row._rawDate, column, item)">
          <div class="flex items-center gap-2 truncate">
            <CalendarIcon :class="taskDueDateToneClass(row._rawDate)" />
            <div :class="taskDueDateToneClass(row._rawDate)" class="truncate">
              {{ dueCellText(row._rawDate, item, column) }}
            </div>
          </div>
        </Tooltip>
        <span
          v-if="isDueOverdue(row._rawDate)"
          class="shrink-0 rounded bg-red-100 px-1.5 py-0.5 text-xs font-medium text-red-800"
        >
          {{ __('Overdue') }}
        </span>
      </div>
      <ListRowItem
        v-else
        :item="item"
        :align="column.align"
        class="overflow-hidden"
      >
        <template #prefix>
          <div v-if="column.key === 'status'" class="flex items-center gap-2">
            <TaskStatusIcon :status="item" />
            <span :class="taskStatusTextClass(item)" class="truncate text-sm">
              {{ __(item) }}
            </span>
          </div>
          <div v-else-if="column.key === 'priority'">
            <TaskPriorityIcon :priority="item" />
          </div>
          <div
            v-else-if="column.key === 'assigned_to' || column.key === 'allocated_to'"
          >
            <Avatar
              v-if="item.full_name"
              class="flex items-center"
              :image="item.user_image"
              :label="item.full_name"
              size="sm"
            />
          </div>
        </template>
        <template #default="{ label }">
          <div
            v-if="['modified', 'creation'].includes(column.key)"
            class="truncate text-base"
            @click="
              (event) =>
                emit('applyFilter', {
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            "
          >
            <Tooltip :text="item.label">
              <div>{{ item.timeAgo }}</div>
            </Tooltip>
          </div>
          <div
            v-else-if="column.type === 'Text Editor'"
            class="line-clamp-2 whitespace-normal break-words text-base text-ink-gray-8"
          >
            {{ htmlToText(item) }}
          </div>
          <router-link
            v-else-if="column.key === 'reference_name' && row.reference_type && row.reference_name"
            :to="referenceRoute(row.reference_type, row.reference_name)"
            class="text-base text-sky-700 hover:underline"
            @click.stop
          >
            {{
              row.reference_type === 'Opportunity'
                ? __('Deal') + ' · ' + row.reference_name
                : __(row.reference_type) + ' · ' + row.reference_name
            }}
          </router-link>
          <div
            v-else-if="column.key === 'reference_name'"
            class="text-base text-ink-gray-5"
          >
            —
          </div>
          <div v-else-if="column.type === 'Check'">
            <FormControl
              type="checkbox"
              :modelValue="item"
              :disabled="true"
              class="text-ink-gray-9"
            />
          </div>
          <div v-else-if="column.key === '_liked_by'">
            <Button
              v-if="column.key == '_liked_by'"
              variant="ghosted"
              :class="isLiked(item) ? 'fill-red-500' : 'fill-white'"
              @click.stop.prevent="
                () => emit('likeDoc', { name: row.name, liked: isLiked(item) })
              "
            >
              <HeartIcon class="h-4 w-4" />
            </Button>
          </div>
          <RatingInput
            v-else-if="column.type === 'Rating'"
            :value="item"
            class="!opacity-100 flex-nowrap overflow-auto"
            :disabled="true"
            :max="column.options || 5"
            @click="
              (event) =>
                emit('applyFilter', {
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            "
          />
          <div
            v-else-if="label"
            class="truncate text-base"
            @click="
              (event) =>
                emit('applyFilter', {
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            "
          >
            {{ getLabel(label, column) }}
          </div>
        </template>
      </ListRowItem>
    </ListRows>
    <ListSelectBanner>
      <template #actions="{ selections, unselectAll }">
        <Dropdown
          :options="listBulkActionsRef.bulkActions(selections, unselectAll)"
        >
          <Button icon="more-horizontal" variant="ghost" />
        </Dropdown>
      </template>
    </ListSelectBanner>
  </ListView>
  <ListFooter
    v-model="pageLengthCount"
    class="border-t px-3 py-2 sm:px-5"
    :options="{
      rowCount: options.rowCount,
      totalCount: options.totalCount,
    }"
    @loadMore="emit('loadMore')"
  />
  <ListBulkActions
    ref="listBulkActionsRef"
    v-model="list"
    doctype="ToDo"
    :options="{
      hideAssign: true,
    }"
  />
</template>
<script setup>
import HeartIcon from '@/components/Icons/HeartIcon.vue'
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/Icons/TaskPriorityIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import RatingInput from '@/components/Controls/RatingInput.vue'
import ListBulkActions from '@/components/ListBulkActions.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
import {
  formatDate,
  isTranslatable,
  formatDuration,
  htmlToText,
  taskDueDateToneClass,
  taskStatusTextClass,
} from '@/utils'
import {
  Avatar,
  ListView,
  ListHeader,
  ListHeaderItem,
  ListSelectBanner,
  ListRowItem,
  ListFooter,
  Dropdown,
  Tooltip,
} from 'frappe-ui'
import { sessionStore } from '@/stores/session'
import { ref, computed, watch } from 'vue'

defineProps({
  rows: { type: Array, required: true },
  columns: { type: Array, required: true },
  options: {
    type: Object,
    default: () => ({
      selectable: true,
      showTooltip: true,
      resizeColumn: false,
      totalCount: 0,
      rowCount: 0,
    }),
  },
})

const emit = defineEmits([
  'loadMore',
  'updatePageCount',
  'showTask',
  'columnWidthUpdated',
  'applyFilter',
  'applyLikeFilter',
  'likeDoc',
  'selectionsChanged',
])

const pageLengthCount = defineModel({ type: Number })
const list = defineModel('list', { type: Object })

function getLabel(label, column) {
  if (column?.key === 'description' && label != null && label !== '') {
    return htmlToText(String(label))
  }
  if (column.type === 'Duration') return formatDuration(label)
  if (column.options && isTranslatable(column.options)) return __(label)
  return label
}

const isLikeFilterApplied = computed(() => {
  return list.value.params?.filters?._liked_by ? true : false
})

const { user } = sessionStore()

function isLiked(item) {
  if (item) {
    let likedByMe = JSON.parse(item)
    return likedByMe.includes(user)
  }
}

watch(pageLengthCount, (val, old_value) => {
  if (val === old_value) return
  emit('updatePageCount', val)
})

const listBulkActionsRef = ref(null)

function isDueDateTimeColumn(column) {
  return column?.type === 'Datetime' || column?.fieldtype === 'Datetime'
}

/** Prefer raw value: list cell `item` is often already formatted; re-formatting breaks Date fields. */
function dueCellText(raw, formattedItem, column) {
  if (raw) {
    if (isDueDateTimeColumn(column)) {
      return formatDate(raw, 'D MMM, YYYY h:mm a')
    }
    return formatDate(raw, '', true)
  }
  return formattedItem || ''
}

function dueTooltipText(raw, column, formattedItem) {
  if (raw) {
    if (isDueDateTimeColumn(column)) {
      return formatDate(raw, 'ddd, D MMM YYYY h:mm a')
    }
    return formatDate(raw, 'dddd, D MMMM YYYY', true)
  }
  return formattedItem ? String(formattedItem) : ''
}

function isDueOverdue(raw) {
  return taskDueDateToneClass(raw) === 'text-red-600 font-medium'
}

function referenceRoute(referenceType, referenceName) {
  if (referenceType === 'Opportunity') {
    return { name: 'Deal', params: { dealId: referenceName } }
  }
  return { name: 'Lead', params: { leadId: referenceName } }
}

defineExpose({
  customListActions: computed(
    () => listBulkActionsRef.value?.customListActions,
  ),
})
</script>
