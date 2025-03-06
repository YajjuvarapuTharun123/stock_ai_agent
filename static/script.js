document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("loading").classList.add("hidden"); // Hide loading initially
});

async function fetchStockData() {
    const ticker = document.getElementById("stockTicker").value;
    const loadingDiv = document.getElementById("loading");
    const stockPlot = document.getElementById("stockPlot");
    const stockSummary = document.getElementById("stockSummary");
    const keyDetailsTable = document.getElementById("keyDetailsData");
    const stockRecommendation = document.getElementById("stockRecommendation");

    // Show loading animation
    loadingDiv.classList.remove("hidden");
    stockPlot.src = "";
    stockSummary.innerHTML = "";
    keyDetailsTable.innerHTML = "";
    stockRecommendation.innerHTML = "";

    try {
        const response = await fetch("/get_stock_data", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ticker: ticker }),
        });

        const data = await response.json();

        if (data.error) {
            stockSummary.innerHTML = `<strong>Error:</strong> ${data.error}`;
        } else {
            stockPlot.src = `data:image/png;base64,${data.stock_plot}`;
            stockSummary.innerHTML = `
                <strong>${data.key_details["Stock Symbol"]}</strong> is currently trading at 
                <strong>${data.key_details["Current Stock Price"]}</strong>. 
                Over the past month, the stock has changed by 
                <strong>${data.key_details["Historical Performance"]["1 Month"]}</strong>. 
                The average 30-day trading volume is 
                <strong>${data.key_details["Volume Changes"]["Average Volume (30D)"]}</strong>, 
                with the most recent volume at <strong>${data.key_details["Volume Changes"]["Current Volume"]}</strong>.
            `;

            // Populate key details table
            Object.entries(data.key_details).forEach(([key, value]) => {
                if (typeof value === "object") {
                    Object.entries(value).forEach(([subKey, subValue]) => {
                        keyDetailsTable.innerHTML += `
                            <tr>
                                <td>${subKey}</td>
                                <td>${subValue}</td>
                            </tr>
                        `;
                    });
                } else {
                    keyDetailsTable.innerHTML += `
                        <tr>
                            <td>${key}</td>
                            <td>${value}</td>
                        </tr>
                    `;
                }
            });

            // Display recommendation
            stockRecommendation.innerHTML = `<strong>${data.recommendation}</strong>`;
        }
    } catch (error) {
        stockSummary.innerHTML = `<strong>Error:</strong> Failed to fetch stock data.`;
    } finally {
        // Hide loading animation
        loadingDiv.classList.add("hidden");
    }
}
