function addItemRow(tableId) {
  const table = document.getElementById(tableId);
  if (!table) return;
  const tbody = table.querySelector("tbody");
  const lastRow = tbody.querySelector("tr:last-child");
  const newRow = lastRow.cloneNode(true);

  newRow.querySelectorAll("input").forEach((input) => {
    input.value = "";
  });
  newRow.querySelectorAll("select").forEach((select) => {
    select.selectedIndex = 0;
  });

  tbody.appendChild(newRow);
}

function removeItemRow(button) {
  const row = button.closest("tr");
  const tbody = row.parentElement;
  if (tbody.children.length > 1) {
    tbody.removeChild(row);
  } else {
    // Just clear values if it's the only row
    row.querySelectorAll("input").forEach((input) => {
      input.value = "";
    });
    row.querySelectorAll("select").forEach((select) => {
      select.selectedIndex = 0;
    });
  }
}

