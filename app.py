from flask import Flask, render_template, request, redirect, send_file, jsonify
import csv
import io

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    bom_data = []
    total_bom_cost = 0

    if request.method == "POST":
        file = request.files.get("csv_file")

        if file and file.filename.endswith(".csv"):
            stream = io.StringIO(file.stream.read().decode("utf-8"))
            csv_reader = csv.DictReader(stream)

            for row in csv_reader:
                qty = int(row.get("Quantity", 0))

                # Example placeholder pricing
                unit_price = 0.72 if qty else 0
                total_price = round(unit_price * qty, 2)
                total_bom_cost += total_price

                bom_data.append({
                    "PartNumber": row.get("PartNumber", ""),
                    "Quantity": qty,
                    "Manufacturer": row.get("Manufacturer", "None"),
                    "Lifecycle": row.get("Lifecycle", "None"),
                    "StockInfo": row.get("Stock", "None"),
                    "UnitPrice": unit_price,
                    "TotalPrice": total_price,
                    "Alternates": row.get("Alternates", "None"),
                    "Error": "None"
                })

            # ✅ store for exporting
            request.session_data = bom_data

        return render_template("index.html", bom=bom_data, total_cost=total_bom_cost)

    return render_template("index.html", bom=None, total_cost=None)


@app.route("/download_results_csv", methods=["POST"])
def download_results_csv():
    bom_data = request.get_json().get("bom", [])

    proxy = io.StringIO()
    writer = csv.writer(proxy)
    writer.writerow([
        "Part Number", "Quantity", "Manufacturer", "Lifecycle",
        "Stock Info", "Unit Price", "Total Price", "Alternates", "Error"
    ])

    for item in bom_data:
        writer.writerow([
            item["PartNumber"],
            item["Quantity"],
            item["Manufacturer"],
            item["Lifecycle"],
            item["StockInfo"],
            item["UnitPrice"],
            item["TotalPrice"],
            item["Alternates"],
            item["Error"]
        ])

    mem = io.BytesIO()
    mem.write(proxy.getvalue().encode("utf-8"))
    mem.seek(0)

    return send_file(
        mem,
        as_attachment=True,
        download_name="BOM_Results.csv",
        mimetype="text/csv"
    )


if __name__ == "__main__":
    app.run(debug=True)
