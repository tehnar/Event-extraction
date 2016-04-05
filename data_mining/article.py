class Article:
    def __init__(self, raw_text="", header="", summary="", text="", site_name="", url="", author_name="", publish_date=None):
        self.raw_text = raw_text
        self.header = header
        self.summary = summary
        self.text = text
        self.site_name = site_name
        self.url = url
        self.author_name = author_name
        self.publish_date = publish_date

