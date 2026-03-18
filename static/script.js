let bom = [
    { component: "Resistor", part: "R-1001", qty: 10 },
    { component: "Capacitor", part: "C-2002", qty: 5 },
    { component: "Inductor", part: "L-3003", qty: 7 },
    { component: "Transistor", part: "T-4004", qty: 12 }
];

function loadTable() {
    const body = document.getElementById("bomBody");
    body.innerHTML = "";

    bom.forEach((item, index) => {
        body.innerHTML += `
        <tr>
            <td>${item.component}</td>
            <td>${item.part}</td>
            <td>${item.qty}</td>
            <td>
                <button class="btn btn-warning btn-sm"
                        onclick="getPrice('${item.part}')">
                    Check Price
                </button>
            </td>
        </tr>`;
    });
}

function addComponent() {
    const comp = document.getElementById("compName").value;
    const part = document.getElementById("partNumber").value;
    const qty = document.getElementById("qty").value;

    if (!comp || !part || !qty) {
        alert("Fill all fields!");
        return;
    }

    bom.push({ component: comp, part: part, qty: qty });
    loadTable();

    document.getElementById("compName").value = "";
    document.getElementById("partNumber").value = "";
    document.getElementById("qty").value = "";
}

async function exportCSV() {
    const res = await fetch("/export_csv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bom })
    });

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "component_bom.csv";
    a.click();
}

async function getPrice(partNumber) {
    const res = await fetch("/mouser_price", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ partNumber })
    });

    const data = await res.json();
    console.log(data);

    alert("Price data fetched. Check console for details.");
}

window.onload = loadTable;
