import os
import io
import json
from flask import render_template, redirect, request, url_for, send_file
from app import app
from app.forms import ProductIdForm
from app.models import Product
import pandas as pd

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/extract")
def display_form():
    form = ProductIdForm()
    return render_template("extract.html", form=form)
 
@app.route("/extract", methods=['POST'])
def extract():
    form = ProductIdForm(request.form)
    if form.validate():
        product_id = form.product_id.data
        product = Product(product_id)
        product.extract_name()
        product.extract_opinions()
        product.calculate_stats()
        product.generate_charts()
        print(product)
        product.save_opinions()
        product.save_info()
        return redirect(url_for('product', product_id=product_id))
    else:
        return render_template("extract.html", form=form)
 
@app.route("/product/<product_id>")
def product(product_id):
    return render_template("product.html", product_id=product_id)
 
@app.route("/charts/<product_id>")
def charts(product_id):
    return render_template("charts.html", product_id=product_id)
 
@app.route("/products")
def products(): #added for the 4th point
    products_data = []
    products_dir = "./app/data/products"
    opinions_dir = "./app/data/opinions"

    for filename in os.listdir(products_dir):
        if filename.endswith(".json"):
            product_id = filename.replace(".json", "")
            with open(os.path.join(products_dir, filename), encoding="utf-8") as f:
                data = json.load(f)
                stats = data.get("stats", {})
                #taking from the stars dictionary needed score:
                stars = stats.get("stars", {})
                total_score = sum(float(star) * count for star, count in stars.items())
                total_count = sum(stars.values())
                average_score = total_score / total_count if total_count > 0 else 0.0
                products_data.append({
                    "product_id": product_id,
                    "product_name": data.get("product_name", "Unknown"),
                    "opinions_count": stats.get("opinions_count", 0),
                    "pros_count": stats.get("pros_count", 0),
                    "cons_count": stats.get("cons_count", 0),
                    "average_score": round(average_score, 2)
                })
    return render_template("products.html", products=products_data)
 
@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/download/<product_id>/<filetype>")
def download_file(product_id, filetype): #added for the 4th point
    opinions_path = f"./app/data/opinions/{product_id}.json"

    if not os.path.exists(opinions_path):
        return "File not found", 404

    with open(opinions_path, encoding="utf-8") as f:
        opinions = json.load(f)

    if not opinions:
        return "No opinions to export", 400

    if filetype == "csv":
        df = pd.DataFrame(opinions)
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode()), mimetype="text/csv", download_name=f"{product_id}.csv", as_attachment=True)

    elif filetype == "xlsx":
        df = pd.DataFrame(opinions)
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return send_file(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", download_name=f"{product_id}.xlsx", as_attachment=True)

    elif filetype == "json":
        output = io.StringIO()
        json.dump(opinions, output, indent=4, ensure_ascii=False)
        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode()), mimetype="application/json", download_name=f"{product_id}.json", as_attachment=True)
    return "Invalid file type", 400