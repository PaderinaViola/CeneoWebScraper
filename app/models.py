import json
import requests
import numpy as np
import pandas as pd
import matplotlib
from bs4 import BeautifulSoup
from matplotlib import pyplot as plt
from config import headers
from app.utils import extract_data, translate_data, create_if_not_exists

matplotlib.use('agg')

class Product:

    def __init__(self, product_id, product_name="", opinions=[], stats={}):
        self.product_id = product_id
        self.product_name = product_name
        self.opinions = opinions
        self.stats = stats

    def __str__(self):
        return f"product_id: {self.product_id}\nproduct_name: {self.product_name}\nstats:"+json.dumps(self.stats, indent=4, ensure_ascii=False)+"\nopinions"+"\n\n".join([str(opinion) for opinion in self.opinions])

    def __repr__(self):
        return f"Product(product_id={self.product_id}, product_name={self.product_name}, opinions=["+", ".join([repr(opinion) for opinion in self.opinions])+f"], stats={self.stats})"

    def get_link(self):
        return f"https://www.ceneo.pl/{self.product_id}#tab=reviews"
    
    def extract_name(self):
        response = requests.get(self.get_link(), headers = headers)
        page_dom = BeautifulSoup(response.text, 'html.parser')
        self.product_name = extract_data(page_dom, "h1")

    def extract_opinions(self):
        url = self.get_link()
        while url:
            response = requests.get(url, headers = headers)
            if response.status_code == 200:
                print(url)
                page_dom = BeautifulSoup(response.text, 'html.parser')
                opinions = page_dom.select("div.js_product-review:not(.user-post--highlight)")
                print(len(opinions))
                for opinion in opinions:
                    single_opinion = Opinion()
                    single_opinion.extract(opinion).translate().transform()
                    self.opinions.append(single_opinion)
                try:
                    url = "https://www.ceneo.pl"+extract_data(page_dom,"a.pagination__next","href")
                except TypeError:
                    url = None

    def opinions_to_dict(self):
        return [opinion.to_dict() for opinion in self.opinions]
    
    def info_to_dict(self):
        return {
            'product_id': self.product_id,
            'product_name': self.product_name,
            'stats': self.stats
        }

    def calculate_stats(self):
        opinions = pd.DataFrame.from_dict(self.opinions_to_dict())
        self.stats["opinions_count"] = opinions.shape[0]
        self.stats["pros_count"] = int(opinions.pros_pl.astype(bool).sum())
        self.stats["cons_count"] = int(opinions.cons_pl.astype(bool).sum())
        self.stats["pros_cons_count"] = int(opinions.apply(lambda o: bool(o.pros_pl) and bool(o.cons_pl), axis=1).sum())
        self.stats["average_stars"] = opinions.stars.mean()
        self.stats["pros"] = opinions.pros_en.explode().value_counts().to_dict()
        self.stats["cons"] = opinions.cons_en.explode().value_counts().to_dict()
        self.stats["recommendations"] = opinions.recommend.value_counts(dropna=False).reindex([True, False, np.nan], fill_value=0).to_dict()
        self.stats["stars"] = opinions.stars.value_counts().reindex(list(np.arange(0.5,5.5,0.5)), fill_value=0).to_dict()

    def generate_charts(self):
        create_if_not_exists("./app/static/pie_charts")
        create_if_not_exists("./app/static/bar_charts")
        recommendations = pd.Series(self.stats['recommendations'], index=self.stats['recommendations'].keys())
        recommendations.plot.pie(
            label = "",
            labels = ["Recommend", "Not recommend", "No opinion"],
            colors = ['turquoise', 'magenta', 'steelblue'],
            autopct = lambda r: f"{r:.1f}%" if r>0 else ""
            )
        plt.title(f"Recommendations for product: {self.product_id}\nTotal number of opinions: {self.stats['opinions_count']}")
        plt.savefig(f"./app/static/pie_charts/{self.product_id}.png")
        plt.close()
 
        plt.figure(figsize=(7,6))
        stars = pd.Series(self.stats['stars'])
        ax = stars.plot.bar(
            color = ["turquoise" if s>3.5 else "magenta" if s<3 else "steelblue" for s in stars.index]
        )
        plt.bar_label(container=ax.containers[0])
        plt.xlabel("Number of stars")
        plt.ylabel("Number of opinions")
        plt.title(f"Number of opinions about product {self.product_id}\nwith particular number of stars\nTotal number of opinions: {self.stats['opinions_count']}")
        plt.xticks(rotation=0)
        plt.savefig(f"./app/static/bar_charts/{self.product_id}.png")
        plt.close()
    
    def save_opinions(self):
        create_if_not_exists("./app/data")
        create_if_not_exists("./app/data/opinions")
        with open(f"./app/data/opinions/{self.product_id}.json", "w", encoding="UTF-8") as jf:
            json.dump(self.opinions_to_dict(), jf, indent=4, ensure_ascii=False)

    def save_info(self):
        create_if_not_exists("./app/data")
        create_if_not_exists("./app/data/products")
        with open(f"./app/data/products/{self.product_id}.json", "w", encoding="UTF-8") as jf:
            json.dump(self.info_to_dict(), jf, indent=4, ensure_ascii=False)

class Opinion:

    selectors = {
        'opinion_id':(None, "data-entry-id"),
        'author':("span.user-post__author-name",),
        'recommend':("span.user-post__author-recomendation > em",),
        'stars':("span.user-post__score-count",),
        'content_pl':("div.user-post__text",),
        'pros_pl':("div.review-feature__item--positive", None, True),
        'cons_pl':("div.review-feature__item--negative", None, True),
        'up_votes':("button.vote-yes","data-total-vote"),
        'down_votes':("button.vote-no","data-total-vote"),
        'published':("span.user-post__published > time:nth-child(1)","datetime"),
        'purchased':("span.user-post__published > time:nth-child(2)","datetime"),
        'content_en': (), 
        'pros_en': (),
        'cons_en': () 
    }

    def __init__(self, opinion_id="", author="", recommend=False, stars=0, content_pl="", pros_pl=[], cons_pl=[], up_votes=0, down_votes=0, published=None, purchased=None, content_en="", pros_en=[], cons_en=[]):
        self.opinion_id = opinion_id
        self.author = author
        self.recommend = recommend
        self.stars = stars
        self.content_pl = content_pl
        self.pros_pl = pros_pl
        self.cons_pl = cons_pl
        self.up_votes = up_votes
        self.down_votes = down_votes
        self.published = published
        self.purchased = purchased
        self.content_en = content_en
        self.pros_en = pros_en
        self.cons_en = cons_en
    
    def __str__(self):
        return "\n".join([f"{key}: {getattr(self,key)}" for key in self.selectors.keys()])
    
    def __repr__(self):
        return "Opinion("+", ".join([f"{key}={getattr(self,key)}" for key in self.selectors.keys()])+")"
    
    def to_dict(self):
        return {key: getattr(self,key) for key in self.selectors.keys()}
    
    def extract(self, opinion):
        for key, values in self.selectors.items():
            setattr(self,key, extract_data(opinion, *values)) 
        return self

    def translate(self):
        self.content_en = translate_data(self.content_pl)
        self.pros_en = [translate_data(pros)  for pros in self.pros_pl]
        self.cons_en = [translate_data(cons)  for cons in self.cons_pl]
        return self

    def transform(self):
        self.recommend = True if self.recommend=="Polecam" else False if self.recommend=="Nie polecam" else None
        self.stars = float(self.stars.split("/")[0].replace(",", "."))
        self.up_votes = int(self.up_votes)
        self.down_votes = int(self.down_votes)
        return self
