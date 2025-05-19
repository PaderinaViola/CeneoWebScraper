import os
import json
import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from matplotlib import pyplot as plt
from config import headers

class Product:

    def __init__(self, product_id, product_name, opinions, stats):
        self.product_id = product_id
        self.product_name = product_name
        self.opinions = opinions
        self.stats = stats

    def __str__(self):
        return f"product_id: {self.product_id}\nproduct_name: {self.product_name}\nstats:"+json.dumps(self.stats, indent=4, ensure_ascii=False)+"\nopinions"+"\n\n".join([str(opinion) for opinion in self.opinions])
    
    def __repr__(self):
        return f"Product(product_id={self.product_id}, product_name={self.product_name}, opinions=["+", ".join(repr(opinion) for opinion in self.opinions)+f"], stats={self.stats})"

    def get_link(self):
        return f"https://www.ceneo.pl/{self.product_id}#tab=reviews"
    
    def extract_name(self):
        response = requests.get(self.get_link(), headers = headers)
        page_dom = BeautifulSoup(response.text, 'html.parser')
        self.product_name = page_dom.select_one("h1")

    def opinions_to_dict(self):
        return [opinion.to_dict() for opinion in self.opinions]

    def calculate_stats(self):
        opinions = pd.DataFrame.from_dict(self.opinions_to_dict())
        self.stats["opinions_count"] = opinions.shape[0]
        self.stats["pros_count"] = opinions.pros_pl.astype(bool).sum()
        self.stats["cons_count"] = opinions.cons_pl.astype(bool).sum()
        self.stats["pros_cons_count"] = opinions.apply(lambda o: bool(o.pros_pl) and bool(o.cons_pl), axis=1).sum()
        self.stats["average_stars"] = opinions.stars.mean()
        self.stats["pros"] = opinions.pros_en.explode().value_counts
        self.stats["cons"] = opinions.cons_en.explode().value_counts
        self.stats["recommendations"] = opinions.recommend.value_counts(dropna=False).reindex([True, False, None], fill_value=0)
        self.stats["stars"] = opinions.stars.value_counts().reindex(list(np.arange(0.5,5.5,0.5)), fill_value=0)

    def generate_charts(self):
        if not os.path.exists("./app/static/pie_charts"):
            os.mkdir("./app/static/pie_charts")
        if not os.path.exists("./app/static/bar_charts"):
            os.mkdir("./app/static/bar_charts")
        self.stats['recommendations'].plot.pie(
            label = "",
            labels = ["Recommend", "Not recommend", "No opinion"],
            colors = ['turquoise', 'blue', 'magenta'],
            autopct = lambda r: f"{r:.1f}%" if r>0 else ""
        )
        plt.title(f"Recommendations for product {self.product_id}\nTotal number of opinions: {self.stats['opinion_count']}")
        plt.savefig(f"./app/static/pie_charts/{self.product_id}.png")
        plt.close()
        plt.figure (figsize=(7,6))
        ax = self.stars.plot.bar(
            color =["violet" if s>3.5 else "forestgreen" if s<3 else "steelblue" for s in self.stars.index]
        )
        plt.bar_label(container=ax.containers[0])
        plt.xlabel("Number of stars")
        plt.ylabel("Number of opinions")
        plt.title(f"Number of opinions about product {self.product_id}\nwith particular number of stars\nTotal number of opinions {self.opinions_count}")
        plt.xticks(rotation=0)
        plt.savefig(f"./bar_charts/{self.product_id}.png")
        plt.close()

class Opinion:
    selectors = {
        'opinion_id':(None, "data-entry-id"),
        'author': ("span.user-post__author-name",),
        'recommend': ("span.user-post__author-recomendation > em",),
        'stars': ("span.user-post__score-count",),
        'content_pl': ("div.user-post__text",),
        'pros_pl': ("div.review-feature__item--positive", None, True),
        'cons_pl': ("div.review-feature__item--negative", None, True),
        "up_votes" :("button.vote-yes","data-total-vote"),
        "down_votes" : ("button.vote-no","data-total-vote"),
        "published" : ("span.user-post__published > time:nth-child(1)","datetime"),
        "purchased" : ("span.user-post__published > time:nth-child(2)","datetime")
    }
    def __init__(self, opinion_id, author, recommend, stars, content, pros, cons, up_votes, down_votes, published, purchased):
        self.opinion_id = opinion_id
        self.author = author
        self.recommend = recommend
        self.stars = stars
        self.content = content
        self.pros = pros
        self.cons = cons
        self.up_votes = up_votes
        self.down_votes = down_votes
        self.published = published
        self.purchased = purchased
    def __str__(self):
        return "\n".join([f"{key}: {getattr(self,key)}" for key in self.selectors.keys()])
    
    def __repr__(self):
        return "Opinon("+", ".join([f"{key}: {getattr(self,key)}" for key in self.selectors.keys()])+")"
    
    def to_dict(self):
        return {key: getattr(self,key) for key in self.selectors.keys()}
    

