from flask import Flask, render_template, request, redirect
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
                # Convert quantity to int
                qty = int(row.get("Quantity", 0))

                # Fake pricing – replace with Mouser API pricing
                unit_price = round(qty * 0.072, 2) if qty else 0
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

        return render_template("index.html",
                               bom=bom_data,
                               total_cost=round(total_bom_cost, 2))

    return render_template("index.html", bom=None, total_cost=None)


if __name__ == "__main__":
    app.run(debug=True)
