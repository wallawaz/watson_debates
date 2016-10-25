import os
import simplejson as json
from watson_developer_cloud import ToneAnalyzerV3

username = os.environ.get("WATSON_TONE_ANALYZER_V3_USERNAME")
password = os.environ.get("WATSON_TONE_ANALYZER_V3_PASSWORD")


class ToneAnalyzer(object):
    def __init__(self,
                 url="https://gateway.watsonplatform.net/tone-analyzer/api",
                 version="2016-05-19"):
        self.username = username
        self.password = password
        self.url = url
        self.version = version
        self.analyzer = None

    def get_analyzer(self):
        self.analyzer = ToneAnalyzerV3(username=self.username,
                                       password=self.password,
                                       version=self.version)

    def run_analyzer(self, content):
        if type(content) == list:
            content_text = ". ".join(content)
        else:
            content_text = content
        response = self.analyzer.tone(content_text, sentences=False)
        if response:
            return response["document_tone"]
        return None
