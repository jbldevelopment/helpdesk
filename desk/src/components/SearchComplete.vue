<template>
  <Autocomplete
    ref="autocompleteRef"
    placeholder="Select an option"
    :options="options"
    :value="selection"
    @update:query="(q) => onUpdateQuery(q)"
    @change="onSelectionChange"
  />
</template>

<script setup lang="ts">
import { Autocomplete } from "@/components";
import { createListResource, createResource } from "frappe-ui";
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

const selection = ref(null);
const autocompleteRef = ref(null);

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

const clientName = createResource({
  url: "frappe.client.get_value",
  params: {
    doctype: "Customer",
    fieldname: "customer_name",
  },
  onSuccess(data) {
    if (data.customer_name) {
      console.log(data.customer_name);
      document.querySelector(".client_name input").value = data.customer_name;
    }
  },
});

function onUpdateQuery(query: string) {
  if (!query && autocompleteRef.value) return;
  if (props.doctype === "HD Ticket Type") {
    const parentTicketType = getParentTicketType();
    r.update({
      filters: {
        [props.searchField]: ["like", `%${query}%`],
        ["parent_ticket_type"]: ["=", parentTicketType],
      },
    });
  } else if (props.doctype === "IO DP Master") {
    const client_id = getClientId();
    r.update({
      filters: {
        ["client_id"]: ["=", client_id],
      },
    });
  } else {
    r.update({
      filters: {
        [props.searchField]: ["like", `%${query}%`],
      },
    });
  }

  r.reload();
}

function onSelectionChange(value) {
  selection.value = value;
  console.log("Selection changed", selection.value);
  if (props.doctype === "Customer" && value) {
    const filters = { ["name"]: ["=", value] };
    console.log("Filters changed", filters);
    clientName.update(filters);
    clientName.setData();
  }
}

watchEffect(() => {
  autocompleteRef.value?.$refs?.search?.$el?.addEventListener(
    "focus",
    async () => {
      if (props.doctype === "HD Ticket Type") {
        const filters = {
          ["parent_ticket_type"]: ["=", getParentTicketType()],
        };
        UpdateQuery(filters);
      } else if (props.doctype === "IO DP Master") {
        const filters = { ["client_id"]: ["=", getClientId()] };
        UpdateQuery(filters);
      } else if (props.doctype === "Customer") {
        const filters = { ["name"]: ["=", getClientId()] };
        clientName.update(filters);
        clientName.reload();
      }
    }
  );
});

function UpdateQuery(filters: any) {
  r.update({ filters });
  r.reload();
}

function getParentTicketType() {
  const parentTicketType = getSelectedOption("parent_ticket_type");
  return parentTicketType;
}

function getClientId() {
  const client_id = getSelectedOption("client_id");
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
