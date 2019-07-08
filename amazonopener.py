import csv
from bs4 import BeautifulSoup
import requests
import sqlite3
from datetime import datetime

def setupDB(cursor):
    cursor.execute('''CREATE TABLE refprices
                (price real, brand text, name text, amName text, locale text, updatedAt text)
                ''')

dbName = 'mobo.db'
conn = sqlite3.connect(dbName)
cur = conn.cursor()
tableName = 'refprices'
force = True

try :
    cur.execute('SELECT * from refprices')
except:
    print('setup {} in DB {}'.format(tableName, dbName))
    setupDB(cur)

headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'
    }

loc = {
    'fr':'fr',
    'de':'de',
    'es':'es',
    'it':'it'
}

currentloc = loc['fr']


with open("AM4Vcore.csv", 'r') as source:
    s = requests.Session()
    s.headers = headers
    r = csv.reader(source, delimiter=',')
    for a in r:
        if a[0] != '' and a[1] == '':
            brand = a[0]
            continue
        if a[1] != 'mATX':
            continue
        print('{} {}'.format(brand, a[0]))  
        refName = a[0]
        for currentLoc in loc.keys():
            url = "https://www.amazon.{local}/s?k=".format(local=loc[currentLoc])
            azurl = "{}{}+{}".format(url,brand, refName.replace(' ', '+'))
            rq = s.get(azurl)
            if rq.raise_for_status():
                print(rq.status_code + ' ' + rq.text)
            soup = BeautifulSoup(rq.text,'html5lib')
            articles = soup.find("span",{'class':'a-size-medium'})
            prices = soup.find('span',{'class':'a-price-whole'})
            if prices == None:
                articles = soup.find("span",{'class':'a-size-medium'})
                prices = soup.find_next('span',{'class':'a-price-whole'})
            if (prices == None or articles == None):
                print("No item found")
            else :
                if force == True or (cur.execute('SELECT amName FROM refprices WHERE locale = "{currentloc}" AND name = "{refname}" '.format(currentloc = currentLoc, refname = refName)).fetchone() == str(articles.contents[0])):
                    print("{price} ---- {item}".format(item=articles.contents[0],price=prices.contents[0]) ) 
                    item = (str(float(prices.contents[0].replace(",","."))), brand, refName, str(articles.contents[0]), currentLoc, datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
                    cur.execute('INSERT INTO refprices VALUES (?,?,?,?,?,?)',item)
                else:
                    print('Different item')
    conn.commit()
    conn.close()