function fetchStockData() {
    let ticker = document.getElementById("stockTicker").value;

    if (!ticker) {
        alert("Please select a stock symbol!");
        return;
    }

    document.getElementById("loading").classList.remove("hidden");
    document.getElementById("analysisData").innerHTML = "";
    document.getElementById("keyDetailsData").innerHTML = "";  // Reset key details table
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
        const analysis = data.analysis.split('\n');
        const analysisTable = document.getElementById("analysisData");
        analysis.forEach(analysisItem => {
            const row = document.createElement('tr');
            const columns = analysisItem.split('|');  
            columns.forEach(col => {
                const cell = document.createElement('td');
                cell.textContent = col.trim();
                row.appendChild(cell);
            });
            analysisTable.appendChild(row);
        });

        // Populate Key Details Table
        const keyDetails = data.key_details;
        const keyDetailsTable = document.getElementById("keyDetailsData");
        for (const detail in keyDetails) {
            const row = document.createElement('tr');
            const cell1 = document.createElement('td');
            const cell2 = document.createElement('td');

            if (typeof keyDetails[detail] === 'object') {
                for (const subDetail in keyDetails[detail]) {
                    const subRow = document.createElement('tr');
                    const subCell1 = document.createElement('td');
                    subCell1.textContent = `${subDetail}`;
                    const subCell2 = document.createElement('td');
                    subCell2.textContent = keyDetails[detail][subDetail];
                    subRow.appendChild(subCell1);
                    subRow.appendChild(subCell2);
                    keyDetailsTable.appendChild(subRow);
                }
            } else {
                cell1.textContent = detail;
                cell2.textContent = keyDetails[detail];
                row.appendChild(cell1);
                row.appendChild(cell2);
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
