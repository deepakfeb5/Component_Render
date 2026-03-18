from flask import Flask, render_template, request, jsonify, send_file
import csv
import io
import requests

app = Flask(__name__)

# Replace with your real Mouser API key
MOUSER_API_KEY = "3f8661d7-e599-45f7-a572-72280fd2f09a"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/export_csv", methods=["POST"])
def export_csv():
    data = request.json.get("bom", [])

    proxy = io.StringIO()
    writer = csv.writer(proxy)
    writer.writerow(["Component", "Part Number", "Quantity"])

    for item in data:
        writer.writerow([item["component"], item["part"], item["qty"]])

    mem = io.BytesIO()
    mem.write(proxy.getvalue().encode("utf-8"))
    mem.seek(0)

    return send_file(
        mem,
        as_attachment=True,
        download_name="component_bom.csv",
        mimetype="text/csv"
    )

@app.route("/mouser_price", methods=["POST"])
def mouser_price():
    part_number = request.json.get("partNumber")

    url = f"https://api.mouser.com/api/v1/search/partnumber?apiKey={MOUSER_API_KEY}"
    payload = {
        "SearchByPartRequest": {
            "mouserPartNumber": part_number
        }
    }

    try:
        response = requests.post(url, json=payload)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
