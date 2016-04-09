import os,requests
from bs4 import BeautifulSoup

# if "cc98_hot" not in os.listdir(os.getcwd()):
#     os.mkdir(os.getcwd() + "/cc98_hot")
# os.chdir(os.getcwd() + "/cc98_hot")
# print(os.getcwd())

html = requests.post("http://www.cc98.org/hottopic.asp")
print(html.text.__sizeof__())

soup = BeautifulSoup(html.text)
print(soup.prettify())
#TODO parse html of cc98 hot