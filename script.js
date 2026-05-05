let chart = null;
let currentPrices = [];

// -------------------------------
// LOAD COMPANIES
// -------------------------------
window.onload = function () {
    fetch("http://127.0.0.1:5000/companies")
        .then(res => {
            if (!res.ok) throw new Error("Server not responding");
            return res.json();
        })
        .then(data => {
            const dropdown = document.getElementById("company");

            dropdown.innerHTML = "<option value=''>Select Company</option>";

            if (data.error) {
                alert(data.error);
                return;
            }

            data.forEach(company => {
                let option = document.createElement("option");
                option.value = company;
                option.text = company;
                dropdown.appendChild(option);
            });
        })
        .catch(err => {
            console.error("❌ Error loading companies:", err);
            alert("🚫 Backend not running! Please start server (python app.py)");
        });
};

// -------------------------------
// LOAD PRICES + GRAPH
// -------------------------------
function loadPrices() {
    const company = document.getElementById("company").value;

    if (!company) return;

    fetch("http://127.0.0.1:5000/get_prices", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({company: company})
    })
    .then(res => {
        if (!res.ok) throw new Error("Failed to fetch prices");
        return res.json();
    })
    .then(data => {

        if (data.error) {
            alert(data.error);
            return;
        }

        currentPrices = data;

        // Format display
        const formatted = data.map((price, index) => {
            return `Day${index + 1}: ${price}`;
        }).join(" | ");

        document.getElementById("prices").value = formatted;

        // Draw chart
        const ctx = document.getElementById("stockChart").getContext("2d");

        if (chart) chart.destroy();

        chart = new Chart(ctx, {
            type: "line",
            data: {
                labels: data.map((_, i) => `Day ${i+1}`),
                datasets: [{
                    label: "Stock Price",
                    data: data,
                    borderWidth: 2
                }]
            }
        });
    })
    .catch(err => {
        console.error("❌ Error loading prices:", err);
        alert("🚫 Backend error while loading prices");
    });
}

// -------------------------------
// PREDICT PRICE
// -------------------------------
function predictPrice() {

    if (currentPrices.length !== 30) {
        alert("⚠️ Prices not loaded properly!");
        return;
    }

    fetch("http://127.0.0.1:5000/predict", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({prices: currentPrices})
    })
    .then(res => {
        if (!res.ok) throw new Error("Prediction failed");
        return res.json();
    })
    .then(data => {

        if (data.error) {
            alert(data.error);
            return;
        }

        const formatted = data.predicted_price.toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });

        document.getElementById("result").innerText = "₹ " + formatted;

        // Update chart with prediction
        if (chart) {
            chart.data.labels.push("Next Day");
            chart.data.datasets[0].data.push(data.predicted_price);
            chart.update();
        }
    })
    .catch(err => {
        console.error("❌ Prediction error:", err);
        alert("🚫 Backend error during prediction");
    });
}