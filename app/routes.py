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
 

 #for scenario 5!!!
@app.route("/product")
def product_a():
    product_name_filter = request.args.get("product_name", "").lower()
    sort_by = request.args.get("sort_by", "product_name")
    order = request.args.get("order", "asc")

    products_data = []
    product_a_dir = "./app/data/products"
    opinion_a_dir = "./app/data/opinions"

    for filename in os.listdir(product_a_dir):
        if filename.endswith(".json"):
            product_id = filename.replace(".json", "")
            with open(os.path.join(product_a_dir, filename), encoding="utf-8") as f:
                data = json.load(f)
                if product_name_filter and product_name_filter not in data.get("product_name", "").lower():
                    continue

                stats = data.get("stats", {})
                stars = stats.get("stars", {})
                total_score = sum(float(star) * count for star, count in stars.items())
                total_count = sum(stars.values())
                average_score = total_score / total_count if total_count > 0 else 0.0

                try:
                    with open(os.path.join(opinion_a_dir, f"{product_id}.json"), encoding="utf-8") as f_op:
                        opinions_data_raw = json.load(f_op)
                        opinions_data = [
                            {"author": op.get("author", "Anonymous"), "content_en": op.get("content_en", "")}
                            for op in opinions_data_raw
                        ]
                except (FileNotFoundError, json.JSONDecodeError):
                    opinions_data = []
            
                products_data.append({
                    "product_id": product_id,
                    "product_name": data.get("product_name", "Unknown"),
                    "opinions_count": stats.get("opinions_count", 0),
                    "opinion_a": opinions_data,
                    "pros_count": stats.get("pros_count", 0),
                    "cons_count": stats.get("cons_count", 0),
                    "average_score": round(average_score, 2)
                })

    # sorting based on column
    products_data.sort(key=lambda x: x.get(sort_by, 0), reverse=(order == "desc"))

    return render_template("product.html", products=products_data, sort_by=sort_by, order=order)

@app.route("/product/<product_id>/charts")
def product_charts(product_id):
    product_file = f"./app/data/products/{product_id}.json"
    if not os.path.exists(product_file):
        return f"Product {product_id} not found", 404

    with open(product_file, encoding="utf-8") as f:
        product_data = json.load(f)

    product_name = product_data.get("product_name", "Unknown")

    pie_chart_path = f"pie_charts/{product_id}.png"
    bar_chart_path = f"bar_charts/{product_id}.png"

    return render_template("charts.html",
                           product_id=product_id,
                           product_name=product_name,
                           pie_chart=pie_chart_path,
                           bar_chart=bar_chart_path)

 
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

#added for the 4th point
@app.route("/download/<product_id>/<filetype>")
def download_file(product_id, filetype): 
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

#added for the 5th point
@app.route("/download_contents/<product_id>/<filetype>")
def download_opinion_contents(product_id, filetype):
    import pandas as pd
    import io
    from flask import send_file

    opinions_path = f"./app/data/opinions/{product_id}.json"

    if not os.path.exists(opinions_path):
        return "File not found", 404

    with open(opinions_path, encoding="utf-8") as f:
        opinions = json.load(f)

    if not opinions:
        return "No opinions to export", 400
    contents = [
        {
            "opinion_id": opinion.get("opinion_id"),
            "content_en": opinion.get("content_en", ""),
            "content_pl": opinion.get("content_pl", "")
        }
        for opinion in opinions
    ]
    if filetype == "csv":
        df = pd.DataFrame(contents)
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode()), mimetype="text/csv", download_name=f"{product_id}_contents.csv", as_attachment=True)

    elif filetype == "xlsx":
        df = pd.DataFrame(contents)
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return send_file(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", download_name=f"{product_id}_contents.xlsx", as_attachment=True)

    elif filetype == "json":
        output = io.StringIO()
        json.dump(contents, output, indent=4, ensure_ascii=False)
        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode()), mimetype="application/json", download_name=f"{product_id}_contents.json", as_attachment=True)

    return "Invalid file type", 400