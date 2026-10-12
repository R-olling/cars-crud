"use strict";

// Plain browser JavaScript. No frontend framework, build step, or template engine.
const errorBox = document.querySelector("#error");

function showError(error) {
  errorBox.textContent = error.message || "Something went wrong. Please try again.";
  errorBox.hidden = false;
}

function clearError() {
  errorBox.textContent = "";
  errorBox.hidden = true;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Accept": "application/json", ...options.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message = Array.isArray(body.detail)
      ? body.detail.map((error) => `${error.loc.at(-1)}: ${error.msg}`).join("; ")
      : body.detail || `Request failed (${response.status}). Please try again.`;
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

function carName(car) {
  return `${car.make} ${car.model}`;
}

async function deleteCar(car, button) {
  if (!window.confirm(`Delete ${carName(car)}? This cannot be undone.`)) return;
  clearError();
  button.disabled = true;
  try {
    await api(`/api/cars/${car.id}`, { method: "DELETE" });
    window.location.assign("/");
  } catch (error) {
    showError(error);
    button.disabled = false;
  }
}

function actionLink(label, href) {
  const link = document.createElement("a");
  link.textContent = label;
  link.href = href;
  return link;
}

async function loadList() {
  try {
    const cars = await api("/api/cars");
    const tbody = document.querySelector("#cars");
    tbody.replaceChildren();
    for (const car of cars) {
      const row = document.createElement("tr");
      for (const value of [car.make, car.model, car.year, car.color || "Not specified"]) {
        const cell = document.createElement("td");
        // Never insert user-provided values with innerHTML.
        cell.textContent = value;
        row.append(cell);
      }
      const actionsCell = document.createElement("td");
      const actions = document.createElement("div");
      actions.className = "actions";
      const deleteButton = document.createElement("button");
      deleteButton.type = "button";
      deleteButton.textContent = "Delete";
      deleteButton.className = "danger";
      deleteButton.addEventListener("click", () => deleteCar(car, deleteButton));
      actions.append(
        actionLink("View", `/cars/${car.id}`),
        actionLink("Edit", `/cars/${car.id}/edit`),
        deleteButton,
      );
      actionsCell.append(actions);
      row.append(actionsCell);
      tbody.append(row);
    }
    document.querySelector("#car-count").textContent = `${cars.length} car${cars.length === 1 ? "" : "s"}`;
    document.querySelector("#empty-state").hidden = cars.length !== 0;
    document.querySelector("#table-wrapper").hidden = cars.length === 0;
  } catch (error) {
    document.querySelector("#car-count").textContent = "Unable to load";
    showError(error);
  }
}

async function loadForm() {
  const match = window.location.pathname.match(/^\/cars\/(\d+)\/edit$/);
  const carId = match ? match[1] : null;
  const form = document.querySelector("#car-form");
  const saveButton = document.querySelector("#save-button");
  const title = carId ? "Edit car" : "Add car";
  document.title = `${title} | My garage`;
  document.querySelector("#page-title").textContent = title;
  saveButton.textContent = carId ? "Save changes" : "Create car";

  if (carId) {
    document.querySelector("#cancel-link").href = `/cars/${carId}`;
    try {
      const car = await api(`/api/cars/${carId}`);
      for (const field of ["make", "model", "year", "color"]) {
        form.elements.namedItem(field).value = car[field];
      }
    } catch (error) {
      showError(error);
      return; // Keep save disabled if loading the existing car failed.
    }
  }

  saveButton.disabled = false;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (saveButton.disabled) return;
    clearError();
    saveButton.disabled = true;
    const data = new FormData(form);
    const payload = {
      make: data.get("make").trim(),
      model: data.get("model").trim(),
      year: Number(data.get("year")),
      color: data.get("color").trim(),
    };
    try {
      const car = await api(carId ? `/api/cars/${carId}` : "/api/cars", {
        method: carId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      window.location.assign(`/cars/${car.id}`);
    } catch (error) {
      showError(error);
      errorBox.focus();
      saveButton.disabled = false;
    }
  });
}

async function loadDetail() {
  const carId = window.location.pathname.split("/")[2];
  const car = await api(`/api/cars/${carId}`);
  const name = carName(car);
  document.title = `${name} | My garage`;
  document.querySelector("#car-title").textContent = name;
  for (const field of ["make", "model", "year", "color"]) {
    document.querySelector(`#car-${field}`).textContent = car[field] || "Not specified";
  }
  document.querySelector("#edit-link").href = `/cars/${car.id}/edit`;
  const deleteButton = document.querySelector("#delete-button");
  deleteButton.addEventListener("click", () => deleteCar(car, deleteButton));
  document.querySelector("#car-detail").hidden = false;
}

async function main() {
  const page = document.body.dataset.page;
  if (page === "list") await loadList();
  if (page === "form") await loadForm();
  if (page === "detail") await loadDetail();
}

main().catch(showError);
