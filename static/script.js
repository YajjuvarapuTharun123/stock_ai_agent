function fetchStockData() {
    let ticker = document.getElementById("stockTicker").value;

    if (!ticker) {
        alert("Please select a stock symbol!");
        return;
    }

    document.getElementById("loading").classList.remove("hidden");
    document.getElementById("analysisData").innerHTML = "";
    document.getElementById("keyDetailsData").innerHTML = "";
    document.getElementById("stockPlot").src = "";

    fetch("/get_stock_data", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker: ticker })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("loading").classList.add("hidden");

        // Populate Analysis Table
        const analysisTable = document.getElementById("analysisData");
        const analysisLines = data.analysis.split("\n");
        analysisLines.forEach(line => {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 3;
            cell.textContent = line.trim();
            row.appendChild(cell);
            analysisTable.appendChild(row);
        });

        // Populate Key Details Table
        const keyDetails = data.key_details;
        const keyDetailsTable = document.getElementById("keyDetailsData");
        for (const detail in keyDetails) {
            if (typeof keyDetails[detail] === 'object') {
                for (const subDetail in keyDetails[detail]) {
                    const row = document.createElement('tr');
                    row.innerHTML = `<td>${subDetail}</td><td>${keyDetails[detail][subDetail]}</td>`;
                    keyDetailsTable.appendChild(row);
                }
            } else {
                const row = document.createElement('tr');
                row.innerHTML = `<td>${detail}</td><td>${keyDetails[detail]}</td>`;
                keyDetailsTable.appendChild(row);
            }
        }

        // Set the plot image
        document.getElementById("stockPlot").src = "data:image/png;base64," + data.stock_plot;
    })
    .catch(error => {
        document.getElementById("loading").classList.add("hidden");
        alert("Error fetching stock data!");
        console.error(error);
    });
}
