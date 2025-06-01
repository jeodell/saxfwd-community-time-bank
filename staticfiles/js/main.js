// Utility function to format dates
function formatDate(dateString) {
  const options = { year: "numeric", month: "long", day: "numeric" };
  return new Date(dateString).toLocaleDateString(undefined, options);
}

// Utility function to format hours
function formatHours(hours) {
  return parseFloat(hours).toFixed(1);
}

// Function to handle form validation
function validateForm(formId) {
  const form = document.getElementById(formId);
  if (!form) return true;

  let isValid = true;
  const requiredFields = form.querySelectorAll("[required]");

  requiredFields.forEach(field => {
    if (!field.value.trim()) {
      field.classList.add("is-invalid");
      isValid = false;
    } else {
      field.classList.remove("is-invalid");
    }
  });

  return isValid;
}

// Function to handle dynamic form fields
function addFormField(containerId, templateId) {
  const container = document.getElementById(containerId);
  const template = document.getElementById(templateId);

  if (!container || !template) return;

  const clone = template.content.cloneNode(true);
  container.appendChild(clone);
}

// Function to remove form fields
function removeFormField(button) {
  const fieldContainer = button.closest(".form-field-container");
  if (fieldContainer) {
    fieldContainer.remove();
  }
}

// Function to handle AJAX form submission
async function submitFormAjax(formId, successCallback, errorCallback) {
  const form = document.getElementById(formId);
  if (!form) return;

  const formData = new FormData(form);

  try {
    const response = await fetch(form.action, {
      method: form.method,
      body: formData,
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    });

    if (!response.ok) {
      throw new Error("Network response was not ok");
    }

    const data = await response.json();
    if (successCallback) {
      successCallback(data);
    }
  } catch (error) {
    if (errorCallback) {
      errorCallback(error);
    }
  }
}

// Function to handle dynamic content loading
async function loadContent(url, targetId) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error("Network response was not ok");
    }

    const content = await response.text();
    const target = document.getElementById(targetId);
    if (target) {
      target.innerHTML = content;
    }
  } catch (error) {
    console.error("Error loading content:", error);
  }
}

// Function to handle notifications
function showNotification(message, type = "info") {
  const notification = document.createElement("div");
  notification.className = `alert alert-${type} alert-dismissible fade show`;
  notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

  const container = document.getElementById("notification-container");
  if (container) {
    container.appendChild(notification);
    setTimeout(() => {
      notification.remove();
    }, 5000);
  }
}

// Initialize tooltips and popovers
document.addEventListener("DOMContentLoaded", function () {
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
  popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });
});
