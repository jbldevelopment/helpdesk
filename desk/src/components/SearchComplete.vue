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
import { useAuthStore } from "@/stores/auth";

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
    changeOptions();

    // Append new data after initial fetch
    let client_id = getclientLogin();
    if (
      client_id &&
      typeof client_id === "string" &&
      props.doctype == "Customer"
    ) {
      r.data.push({
        name: client_id,
      });
      if (!selection.value) {
        selection.value = options.value.find((o) => o.value === client_id);
        updateClientFilter({
          name: client_id,
        });
      }
    } else {
      selection.value = props.value
        ? options.value.find((o) => o.value === props.value)
        : null;
    }
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
const authStore = useAuthStore();

function createResourceForField(fieldname, selector) {
  return createResource({
    url: "frappe.client.get_value",
    params: {
      doctype: "Customer",
      fieldname: fieldname,
    },
    onSuccess(data) {
      if (data[fieldname]) {
        const inputElement = document.querySelector(selector);
        if (inputElement) {
          inputElement.value = data[fieldname];
          inputElement.dispatchEvent(new Event("input"));
          inputElement.dispatchEvent(new Event("change"));
        }
      }
    },
  });
}

const client_data = createResource({
  url: "frappe.client.get_value",
  params: {
    doctype: "User",
    fieldname: "customer",
    filters: {
      name: ["=", authStore.userId],
    },
  },
  transform(data) {
    if (data["customer"]) {
      let client_id = data["customer"];
      return client_id;
    }
  },
});

const clientName = createResourceForField(
  "customer_name",
  ".client_name input"
);
const existingPan = createResourceForField("pan", ".existing_pan input");
const existingGuardianName = createResourceForField(
  "guardian_name",
  ".existing_guardian_name input"
);
const existingDOB = createResourceForField("dob", ".existing_dob input");
const existingSeconHolder = createResourceForField(
  "second_holder_name",
  ".existing_second_holder_name input"
);
const existingThirdHolder = createResourceForField(
  "third_holder_name",
  ".existing_third_holder_name input"
);
const existingKartaName = createResourceForField(
  "karta_name",
  ".existing_karta_name input"
);
const existingNRIType = createResourceForField(
  "nri_type",
  ".existing_nri_type input"
);

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
    const parentTicketType = getTicketType();
    let filters = {
      [props.searchField]: ["like", `%${query}%`],
      ["disabled"]: ["=", 0],
    };
    let client_id = getclientLogin();
    if (client_id instanceof Object && client_id["customer"]) {
      filters["branch_code"] = ["=", client_id["customer"]];
    } else if (client_id && typeof client_id === "string") {
      filters["branch_code"] = ["=", client_id];
    }
    if (parentTicketType == "NRI to Resident Indian Account Status Change") {
      filters["customer_group"] = ["=", "Non Resident Indian"];
    } else if (
      parentTicketType == "Resident Indian/NRE to NRO Account Status Change"
    ) {
      filters["customer_group"] = [
        "in",
        ["Resident Individual", "Non Resident External"],
      ];
    }
    r.update({
      filters: filters,
    });
  } else if (autocompleteRef.value && props.doctype === "Bank Account") {
    const client_id = getClientId();
    r.update({
      filters: {
        ["party_type"]: ["=", "Customer"],
        ["party"]: ["=", client_id],
        ["disabled"]: ["=", 0],
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
      changeOptions();
    }
  );
});

function changeOptions() {
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
  } else if (autocompleteRef.value && props.doctype === "Bank Account") {
    let filters = {
      ["party_type"]: ["=", "Customer"],
      ["party"]: ["=", getClientId()],
      ["disabled"]: ["=", 0],
    };
    UpdateQuery(filters);
  } else if (autocompleteRef.value && props.doctype == "Customer") {
    let client_id = getclientLogin();
    let filters = {
      ["disabled"]: ["=", 0],
    };
    if (client_id instanceof Object && client_id["customer"]) {
      filters["branch_code"] = ["=", client_id["customer"]];
    } else if (client_id && typeof client_id === "string") {
      filters["branch_code"] = ["=", client_id];
    }
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
  existingPan.update({
    params: {
      doctype: "Customer",
      fieldname: "pan",
      filters: filters,
    },
  });
  existingPan.reload();
  existingGuardianName.update({
    params: {
      doctype: "Customer",
      fieldname: "guardian_name",
      filters: filters,
    },
  });
  existingGuardianName.reload();
  existingDOB.update({
    params: {
      doctype: "Customer",
      fieldname: "dob",
      filters: filters,
    },
  });
  existingDOB.reload();
  existingSeconHolder.update({
    params: {
      doctype: "Customer",
      fieldname: "second_holder_name",
      filters: filters,
    },
  });
  existingSeconHolder.reload();
  existingThirdHolder.update({
    params: {
      doctype: "Customer",
      fieldname: "third_holder_name",
      filters: filters,
    },
  });
  existingThirdHolder.reload();
  existingKartaName.update({
    params: {
      doctype: "Customer",
      fieldname: "karta_name",
      filters: filters,
    },
  });
  existingKartaName.reload();
  existingNRIType.update({
    params: {
      doctype: "Customer",
      fieldname: "nri_type",
      filters: filters,
    },
  });
  existingNRIType.reload();
}

function getParentTicketType() {
  // Get selected parent ticket type
  const parentTicketType = getSelectedOption("parent_ticket_type");
  return parentTicketType;
}

function getTicketType() {
  // Get selected ticket type
  const TicketType = getSelectedOption("ticket_type");
  return TicketType;
}

function getClientId() {
  // Get selected client id
  let client_id = getSelectedOption("client_id");
  if (client_id && client_id != "Select an option") return client_id;
}

function getclientLogin() {
  client_data.reload();
  return client_data.data;
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
