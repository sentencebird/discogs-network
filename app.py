import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network
import json 
import oauth2 as oauth

class Discogs():
    def __init__(self):
        consumer_key = os.environ['CONSUMER_KEY']
        consumer_secret = os.environ['CONSUMER_SECRET']
        token_key = os.environ['TOKEN_KEY']
        token_secret = os.environ['TOKEN_SECRET']        
        consumer = oauth.Consumer(consumer_key, consumer_secret)
        token = oauth.Token(key=token_key, secret=token_secret)
        self.client = oauth.Client(consumer, token)
        self.base_url = 'https://api.discogs.com/'
        self.user_agent = 'discogs_api_example/1.0'
        
    def search(self, q, type_="master"):
        res, content = self.client.request(f'{self.base_url}database/search?type={type_}&q={q}', headers={'User-Agent': self.user_agent})
        releases = json.loads(content.decode('utf-8'))
        return releases['results'] if 'results' in releases else []
        
    def fetch_master(self, master_id):
        res, content = self.client.request(f'{self.base_url}masters/{master_id}', headers={'User-Agent': self.user_agent})
        return  json.loads(content.decode('utf-8'))
    
    def fetch_artist(self, artist_id):
        res, content = self.client.request(f'{self.base_url}artists/{artist_id}', headers={'User-Agent': self.user_agent})
        return  json.loads(content.decode('utf-8'))

    
class ArtistsNetwork():
    def __init__(self, discogs):
        self.network = Network(width="100%")
        self.next_nodes_artists = []
        self.appended_artists_ids = []
        self.discogs = discogs
        self.max_artists_per_artist = 5

    def _add_artists_nodes(self, artist, is_last_depth=False): # これがfetch_artistの結果
        nodes = artist["members"] if "members" in artist else artist["groups"]
        nodes = nodes[:self.max_artists_per_artist]
        self.next_nodes_artists = [a for a in self.next_nodes_artists if "id" in a and a["id"] != artist["id"]]
        
        for node in nodes:
            if node["active"]:
                if not is_last_depth and node["id"] not in self.appended_artists_ids:
                    next_artist = discogs.fetch_artist(node["id"])
                    self.next_nodes_artists.append(next_artist)
                self.network.add_node(node["name"], image=node["thumbnail_url"], shape="circularImage", title=f"<a href=\"{node['uri']}\" target='_parent'>詳細</a>")
                self.network.add_edge(artist["name"], node["name"])
                
                self.appended_artists_ids.append(node["id"])

    def create_network(self, origin_artist, max_depth=4):
        self.network.add_node(origin_artist["name"], image=origin_artist["images"][0]["uri150"], shape="circularImage")
        self.next_nodes_artists.append(origin_artist)
            
        for depth in range(max_depth):
            for artist in self.next_nodes_artists:
                if not ("active" in artist and artist["active"]):
                    self._add_artists_nodes(artist, is_last_depth=depth==max_depth)    
    

st.title("グループ相関図")                    
discogs = Discogs()

q = st.text_input("", "Beatles")

search = st.button("検索")

if search:
    results = discogs.search(q, type_="artist")[:5]
    result = results[0]
    st.image(result["thumb"])
    st.write(result["title"])
    artist_id = result["id"]
    
    with st.spinner("作成中"):
        an = ArtistsNetwork(discogs)
        origin_artist = discogs.fetch_artist(artist_id)
        an.create_network(origin_artist)
        an.network.show(f"output_{result["id"]}.html")

        html_file = open(f"output.html_{result["id"]}", 'r', encoding='utf-8')
        source_code = html_file.read() 
        components.html(source_code, height=1200, width=1000)