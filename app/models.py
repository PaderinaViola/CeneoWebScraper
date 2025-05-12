class Product:
    def __init__(self):
        pass

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
