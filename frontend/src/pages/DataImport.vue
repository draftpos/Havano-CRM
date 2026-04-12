<template>
  <DataImport
    :doctype="route.params.doctype"
    :importName="route.params.importName"
    :doctypeMap="doctypeMap"
  />
</template>

<script setup>
import { usePageMeta } from 'frappe-ui'
import { DataImport } from 'frappe-ui/frappe'
import { useRoute } from 'vue-router'

const route = useRoute()

const doctypeMap = {
  'Lead': {
    title: 'Leads',
    listRoute: '/havano-crm/leads',
    pageRoute: `/havano-crm/leads/docname`,
  },
  'Opportunity': {
    title: 'Deals',
    listRoute: '/havano-crm/deals',
    pageRoute: `/havano-crm/deals/docname`,
  },
  Contact: {
    title: 'Contacts',
    listRoute: '/havano-crm/contacts',
    pageRoute: `/havano-crm/contacts/docname`,
  },
  'ToDo': {
    title: 'Todo',
    listRoute: '/havano-crm/tasks',
  },
  'Customer': {
    title: 'Organizations',
    listRoute: '/havano-crm/organizations',
    pageRoute: `/havano-crm/organizations/docname`,
  },
  'Call Log': {
    title: 'Call Log',
    listRoute: '/havano-crm/call-logs',
  },
}

usePageMeta(() => {
  return {
    title: __('Data Import'),
  }
})
</script>
