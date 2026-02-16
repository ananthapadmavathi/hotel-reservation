async function loadStatus() {
  try {
    const res = await fetch("/rooms/status");
    const data = await res.json();
    renderGrid(data);
  } catch (err) {
    console.error("Backend error (status)", err);
    alert("Backend unreachable");
  }
}

function parseInput(value) {
  value = value.trim();

  // Check RANGE format X-Y
  if (value.includes("-")) {
    const parts = value.split("-");
    if (parts.length !== 2) return { error: "Invalid range format" };

    let start = parseInt(parts[0]);
    let end = parseInt(parts[1]);

    if (isNaN(start) || isNaN(end))
      return { error: "Invalid range digits" };

    if (start > end)
      return { error: "Reversed range not allowed (e.g. 5-3)" };

    let count = end - start + 1;

    if (count < 1)
      return { error: "Invalid range" };

    if (count > 5)
      return { error: "Bulk booking limit exceeded (max 5 rooms)" };

    return { type: "bulk", count };
  }

  // Check pure number
  let num = parseInt(value);

  if (isNaN(num)) return { error: "Invalid input" };
  if (num < 1) return { error: "Invalid input" };

  // Single room case (>=100)
  if (num >= 100) return { type: "single", room: num };

  // Bulk case (1-5)
  if (num > 5)
    return { error: "Bulk booking limit exceeded (max 5 rooms)" };

  return { type: "bulk", count: num };
}

async function bookRoom() {
  const input = document.getElementById("roomInput").value;
  if (!input) {
    alert("Enter a value");
    return;
  }

  const parsed = parseInput(input);

  if (parsed.error) {
    alert(parsed.error);
    return;
  }

  let url = "/book";

  let value;
  if (parsed.type === "single") value = parsed.room;
  else value = parsed.count;

  const res = await fetch(`${url}?value=${value}`, { method: "POST" });

  if (!res.ok) {
    const msg = await res.json();
    alert(msg.detail || "Booking failed");
  }

  await loadStatus();
}

async function randomFill() {
  await fetch("/random", { method: "POST" });
  await loadStatus();
}

async function resetHotel() {
  await fetch("/reset", { method: "POST" });
  await loadStatus();
}

function renderGrid(data) {
  const grid = document.getElementById("hotelGrid");
  grid.innerHTML = "";

  for (let floor = 10; floor >= 1; floor--) {
    const row = document.createElement("div");
    row.classList.add("floor-row");

    const label = document.createElement("span");
    label.classList.add("floor-label");
    label.innerText = `Floor ${floor}`;
    row.appendChild(label);

    for (let r of data[floor]) {
      const div = document.createElement("div");
      div.classList.add("room");
      div.innerText = r.room;

      if (r.occupied) {
        div.classList.add("occupied");
        div.onclick = () => openVacateModal(r.booking_id, r.room);
      }

      row.appendChild(div);
    }

    grid.appendChild(row);
  }
}

function openVacateModal(bid, room) {
  document.getElementById("modalTitle").innerText = `Vacate Booking #${bid}?`;
  document.getElementById("modalRoom").innerText = `Room: ${room}`;
  document.getElementById("vacateModal").style.display = "flex";

  document.getElementById("confirmVacateBtn").onclick = async () => {
    await fetch(`/vacate?bid=${bid}`, { method: "POST" });
    closeModal();
    await loadStatus();
  };

  document.getElementById("cancelVacateBtn").onclick = closeModal;
}

function closeModal() {
  document.getElementById("vacateModal").style.display = "none";
}

loadStatus();
