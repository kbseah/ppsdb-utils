import json
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login

wbi_config["MEDIAWIKI_API_URL"] = "https://ppsdb.wikibase.cloud/w/api.php"
wbi_config["SPARQL_ENDPOINT_URL"] = "https://ppsdb.wikibase.cloud/query/sparql"
wbi_config["WIKIBASE_URL"] = "https://ppsdb.wikibase.cloud"
wbi_config['MEDIAWIKI_INDEX_URL'] = 'https://ppsdb.wikibase.cloud/w/index.php'
wbi_config['MEDIAWIKI_REST_URL'] = 'https://ppsdb.wikibase.cloud/w/rest.php',

with open("secrets/bot_password.json", "r") as fh:
    pw = json.load(fh)
login = wbi_login.Login(user=pw["user"], password=pw["password"])

sparql_prefixes = """
PREFIX pp: <https://ppsdb.wikibase.cloud/entity/>
PREFIX ppt: <https://ppsdb.wikibase.cloud/prop/direct/>
PREFIX pps: <https://ppsdb.wikibase.cloud/prop/>
PREFIX ppss: <https://ppsdb.wikibase.cloud/prop/statement/>
PREFIX ppsq: <https://ppsdb.wikibase.cloud/prop/qualifier/>
PREFIX ppsr: <https://ppsdb.wikibase.cloud/prop/reference/>
"""
