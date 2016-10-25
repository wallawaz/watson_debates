import argparse
import bs4
import simplejson as json
import re
import requests
import os
import pickle

from tone import ToneAnalyzer

parser = argparse.ArgumentParser()
parser.add_argument("url", help="webpage storing transcript text")
parser.add_argument("--json", help="dump `tone` to JSON", action="store_true")
args = parser.parse_args()

# i've been using Washington Post
def parse_article(article):
    transcript = {
        "CLINTON": {
            "dialog": [],
        },
        "TRUMP": {
            "dialog": [],
        },
        "HOLT": {
            "dialog": [],
        },
        "COOPER": {
            "dialog": [],
        },
        "RADDATZ": {
            "dialog": [],
        },
        "WALLACE": {
            "dialog": [],
        },
    }
    def _key_to_re(k):
        return r"{k}\: ".format(k=k)

    soup = bs4.BeautifulSoup(article, "html.parser")

    paragraphs = soup.find_all("p")

    speaker = None
    for p in paragraphs:
        found_name = None
        text = p.text
        avoid = False
        for name in transcript:
            search = _key_to_re(name)
            found_name = re.match(search, text)
            if found_name:
                speaker = name
                text_with_speaker_removed = re.sub(search, "", text)
                transcript[name]["dialog"].append(text_with_speaker_removed)
                break

        if found_name == None:
            # new paragraph tag without `NAME:`
            # but the same person is speaking.
            if speaker:
                # do not want `(CROSSTALK), (APPLAUSE), (LAUGHTER)` ..etc
                chatter = re.match(r"\([A-Z]*\)", text)
                if chatter == None:
                    transcript[speaker]["dialog"].append(text)

    # check for multiple speakers in same <p>
    for name in transcript:
        if name == "TRUMP":
            other = "CLINTON:"
        elif name == "CLINTON":
            other = "TRUMP:"
        else:
            other = None

        if other:
            d2 = []
            for d in transcript[name]["dialog"]:
                multiple_speakers = re.findall(other, d)
                if not multiple_speakers:
                    d2.append(d)

            transcript[name]["dialog"] = []
            transcript[name]["dialog"] = d2

    return transcript


def get_url_article_name(url):
    url_parts = url.split("/")
    if url_parts[-1] == "":
        url_parts.pop(-1)
    return url_parts[-1]

def check_article_saved(url):
    article = get_url_article_name(url)
    transcript_name = article + ".pkl"
    return os.path.exists("data/" + transcript_name)

def save_article(url):
    resp = requests.get(url)
    status = resp.status_code
    if status == 200:
        content = resp.content
        article = get_url_article_name(url)
        with open("data/%s.pkl" % article, "wb") as output:
            pickle.dump(content, output)
    else:
        return

def open_article(url):
    article = get_url_article_name(url)
    pickled_article = open("data/%s.pkl" % article, "r")
    data = pickle.load(pickled_article)
    pickled_article.close()
    return data


def check_transcript_tone(url):
    article = get_url_article_name(url)
    tone_name = article + "_tone.pkl"
    return os.path.exists("output/" + tone_name)


def main(url):
    saved = check_article_saved(url)
    article_name = get_url_article_name(url)
    if not saved:
        print "article not saved yet: %s" % url
        save_article(url)
    article = open_article(url)

    have_tone = check_transcript_tone(url)

    if have_tone == False:
        print "watson tone analysis not yet performed"
        watson_tone_analyzer = ToneAnalyzer()
        watson_tone_analyzer.get_analyzer()

        transcript = parse_article(article)

        for name in transcript:
            if transcript[name]["dialog"]:
                response = watson_tone_analyzer.run_analyzer(transcript[name]["dialog"])
                if response:
                    transcript[name]["tone"] = response

        transcript_tone = article_name + "_tone.pkl"
        with open("output/" + transcript_tone, "wb") as output:
            pickle.dump(transcript, output)

    else:
        with open("output/" + article_name + "_tone.pkl", "r") as saved:
            transcript = pickle.load(saved)

        if args.json:
            out = {}
            for k, v in transcript.items():
                if "tone" in v:
                    out[k] = v["tone"]
            if out:
                f = get_url_article_name(url) + ".json"
                with open("output/" + f, "wb") as output:
                    output.write(json.dumps(out))

        for speaker in transcript:
            if "tone" in transcript[speaker]:
                print speaker
                print transcript[speaker]["tone"]


if __name__== "__main__":
    transcript = main(args.url)
