class Article:
    def __init__(self, raw_text="", header="", summary="", text="", url="", author_name="", publish_date=None):
        self.raw_text = raw_text
        self.header = header
        self.summary = summary
        self.text = text
        self.url = url
        self.author_name = author_name
        self.publish_date = publish_date

