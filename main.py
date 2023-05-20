import csv
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
@cross_origin()
def homePage():
    return render_template("index.html")

@app.route('/review', methods=['POST', 'GET'])
@cross_origin()
def index():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ", "")
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString
            uClient = uReq(flipkart_url)
            flipkartPage = uClient.read()
            uClient.close()
            flipkart_html = bs(flipkartPage, "html.parser")
            bigboxes = flipkart_html.find_all("div", {"class": "_1AtVbE col-12-12"})
            del bigboxes[0:3]
            box = bigboxes[0]
            productLink = "https://www.flipkart.com" + box.div.div.div.a['href']
            prodRes = requests.get(productLink)
            prodRes.encoding = 'utf-8'
            prod_html = bs(prodRes.text, "html.parser")
            total_reviews = prod_html.find('span', {'class': '_2_R_DZ'}).text
            total_reviews = int(total_reviews.split()[0].replace(',', ''))
            
            reviews = []
            page_limit = min(total_reviews, 100)  # Limit the number of reviews to scrape
            page = 1
            while len(reviews) < page_limit:
                review_url = f"{productLink}&page={page}"
                review_res = requests.get(review_url)
                review_html = bs(review_res.text, "html.parser")
                commentboxes = review_html.find_all('div', {'class': "_16PBlm"})

                for commentbox in commentboxes:
                    try:
                        name = commentbox.div.div.find_all('p', {'class': '_2sc7ZR _2V5EHH'})[0].text
                    except:
                        name = 'No Name'

                    try:
                        rating = commentbox.div.div.div.div.text
                    except:
                        rating = 'No Rating'

                    try:
                        commentHead = commentbox.div.div.div.p.text
                    except:
                        commentHead = 'No Comment Heading'

                    try:
                        comtag = commentbox.div.div.find_all('div', {'class': ''})
                        custComment = comtag[0].div.text
                    except Exception as e:
                        print("Exception while creating dictionary: ", e)

                    mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead,
                              "Comment": custComment}
                    reviews.append(mydict)

                page += 1

            filename = searchString + ".csv"
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ["Product", "Name", "Rating", "CommentHead", "Comment"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(reviews)

            return render_template('results.html', reviews=reviews)
        except Exception as e:
            print('The Exception message is: ', e)
            return 'Something went wrong'
    else:
        return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
