import { computed } from 'vue'
import PinIcon from '@/components/Icons/PinIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import { viewsStore } from '@/stores/views'

function getIcon(routeName, icon) {
  if (icon) return icon
  switch (routeName) {
    case 'Leads':
      return LeadsIcon
    case 'Deals':
      return DealsIcon
    case 'Contacts':
      return ContactsIcon
    case 'Organizations':
      return OrganizationsIcon
    case 'Notes':
      return NoteIcon
    case 'Call Logs':
      return PhoneIcon
    case 'Tasks':
      return TaskIcon
    default:
      return PinIcon
  }
}

function parseView(views) {
  return views.map((view) => ({
    label: view.label,
    icon: getIcon(view.route_name, view.icon),
    to: {
      name: view.route_name,
      params: { viewType: view.type || 'list' },
      query: { view: view.name },
    },
  }))
}

function filterLink(link) {
  if (link.condition) {
    return link.condition()
  }
  return true
}

const overviewLinks = [
  { label: 'Todo', icon: TaskIcon, to: 'Tasks' },
  { label: 'Dashboard', icon: LucideLayoutDashboard, to: 'Dashboard' },
  { label: 'Calendar', icon: CalendarIcon, to: 'Calendar' },
]

const salesLinks = [
  { label: 'Leads', icon: LeadsIcon, to: 'Leads' },
  { label: 'Deals', icon: DealsIcon, to: 'Deals' },
  { label: 'Contacts', icon: ContactsIcon, to: 'Contacts' },
  { label: 'Organizations', icon: OrganizationsIcon, to: 'Organizations' },
]

const workspaceLinks = [
  { label: 'Notes', icon: NoteIcon, to: 'Notes' },
  { label: 'Call Logs', icon: PhoneIcon, to: 'Call Logs' },
]

export function useNexusAllViews() {
  const { getPinnedViews, getPublicViews } = viewsStore()

  return computed(() => {
    let _views = [
      {
        name: 'Overview',
        hideLabel: false,
        opened: true,
        views: overviewLinks.filter(filterLink),
      },
      {
        name: 'Sales',
        hideLabel: false,
        opened: true,
        views: salesLinks.filter(filterLink),
      },
      {
        name: 'Workspace',
        hideLabel: false,
        opened: true,
        views: workspaceLinks.filter(filterLink),
      },
    ]
    if (getPublicViews().length) {
      _views.push({
        name: 'Public Views',
        opened: true,
        views: parseView(getPublicViews()),
      })
    }
    if (getPinnedViews().length) {
      _views.push({
        name: 'Pinned Views',
        opened: true,
        views: parseView(getPinnedViews()),
      })
    }
    return _views
  })
}
