<template>
  <Autocomplete
    ref="autocompleteRef"
    placeholder="Select an option"
    :options="options"
    :value="selection"
    @update:query="(q) => onUpdateQuery(q)"
    @change="(v) => onSelectionChange(v)"
  />
</template>

<script setup lang="ts">
import { Autocomplete } from "@/components";
import { createResource, createListResource } from "frappe-ui";
import { computed, ref, watchEffect } from "vue";

const props = defineProps({
  value: {
    type: String,
    required: false,
    default: "",
  },
  doctype: {
    type: String,
    required: true,
  },
  searchField: {
    type: String,
    required: false,
    default: "name",
  },
  labelField: {
    type: String,
    required: false,
    default: "name",
  },
  valueField: {
    type: String,
    required: false,
    default: "name",
  },
  pageLength: {
    type: Number,
    required: false,
    default: 1000,
  },
});

const r = createListResource({
  doctype: props.doctype,
  pageLength: props.pageLength,
  orderBy: "name asc",
  auto: true,
  fields: [props.labelField, props.searchField, props.valueField],
  filters: {
    [props.searchField]: ["like", `%${props.value}%`],
  },
  onSuccess: () => {
    selection.value = props.value
      ? options.value.find((o) => o.value === props.value)
      : null;
  },
});
const options = computed(
  () =>
    r.data?.map((result) => ({
      label: result[props.labelField],
      value: result[props.valueField],
    })) || []
);
const selection = ref(null);
const autocompleteRef = ref(null);

const clientName = createResource({
  url: "frappe.client.get_value",
  params: {
    doctype: "Customer",
    fieldname: "customer_name",
  },
  onSuccess(data) {
    if (data.customer_name) {
      const inputElement = document.querySelector("#frappe-ui-2");
      if (inputElement) {
        inputElement.value = data.customer_name;
        inputElement.dispatchEvent(new Event("input"));
        inputElement.dispatchEvent(new Event("change"));
      }
    }
  },
});

function onUpdateQuery(query: string) {
  if (!query && autocompleteRef.value) return;

  if (autocompleteRef.value && props.doctype === "HD Ticket Type") {
    const parentTicketType = getParentTicketType();
    r.update({
      filters: {
        [props.searchField]: ["like", `%${query}%`],
        ["parent_ticket_type"]: ["=", parentTicketType],
        ["disabled"]: ["!=", 1],
      },
    });
  } else if (autocompleteRef.value && props.doctype === "IO DP Master") {
    const client_id = getClientId();
    r.update({
      filters: {
        ["client_id"]: ["=", client_id],
      },
    });
  } else if (autocompleteRef.value && props.doctype === "Customer") {
    r.update({
      filters: {
        [props.searchField]: ["like", `%${query}%`],
      },
    });
  } else if (
    autocompleteRef.value &&
    props.doctype == "HD Parent Ticket Type"
  ) {
    let filters = {
      ["disabled"]: ["!=", 1],
    };
    UpdateQuery(filters);
  } else {
    r.update({
      filters: {
        [props.searchField]: ["like", `%${query}%`],
      },
    });
  }

  r.reload();
}

function onSelectionChange(value_: any) {
  selection.value = value_;

  if (props.doctype === "Customer" && value_) {
    updateClientFilter({
      name: value_.value,
    });
  }
}

watchEffect(() => {
  autocompleteRef.value?.$refs?.search?.$el?.addEventListener(
    "focus",
    async () => {
      if (autocompleteRef.value && props.doctype === "HD Ticket Type") {
        let filters = {
          ["parent_ticket_type"]: ["=", getParentTicketType()],
          ["disabled"]: ["!=", 1],
        };
        UpdateQuery(filters);
      } else if (autocompleteRef.value && props.doctype === "IO DP Master") {
        let filters = {
          ["client_id"]: ["=", getClientId()],
        };
        UpdateQuery(filters);
      } else if (
        autocompleteRef.value &&
        props.doctype == "HD Parent Ticket Type"
      ) {
        let filters = {
          ["disabled"]: ["!=", 1],
        };
        UpdateQuery(filters);
      }
    }
  );
});

function UpdateQuery(filters: any) {
  r.update({
    filters: filters,
  });

  r.reload();
}

function updateClientFilter(filters: any) {
  clientName.update({
    params: {
      doctype: "Customer",
      fieldname: "customer_name",
      filters: filters,
    },
  });
  clientName.reload();
}

function getParentTicketType() {
  // Get selected parent ticket type
  const parentTicketType = getSelectedOption("parent_ticket_type");
  return parentTicketType;
}

function getClientId() {
  // Get selected client id
  let client_id = getSelectedOption("client_id");
  return client_id;
}

function getSelectedOption(class_name: string) {
  const $wrapper = document.querySelector(`.${class_name}`);
  if (!$wrapper) {
    return;
  }

  const selectedOption = $wrapper.innerText;

  if (!selectedOption) {
    return;
  }

  const selectedValue = selectedOption.split("\n").pop().trim();
  return selectedValue;
}
</script>
