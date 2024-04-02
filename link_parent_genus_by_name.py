#!/usr/bin/env python
# coding: utf-8

import json
import argparse

from wikibaseintegrator import wbi_login, WikibaseIntegrator, datatypes, wbi_helpers
from common import wbi_config, login, sparql_prefixes

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dryrun", action="store_true")
    args = parser.parse_args()

    query = """
    SELECT DISTINCT ?qid ?P29 WHERE {
      {
        SELECT DISTINCT ?item ?qid ?itemLabel ?maybeGenus WHERE {
          ?item ppt:P19 ?symbiont.
          FILTER(NOT EXISTS { ?item ppt:P29 ?parent. })
          BIND(ENCODE_FOR_URI(REPLACE(STR(?item), ".*Q", "Q")) AS ?qid)
          SERVICE wikibase:label {
            bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en".
            ?item rdfs:label ?itemLabel.
          }
          BIND(STRBEFORE(?itemLabel, " ") AS ?maybeGenus)
        }
      }
      {
        SELECT DISTINCT ?item2 ?item2Label WHERE {
          ?item2 ppt:P32 pp:Q601;
            rdfs:label ?item2Label.
          FILTER((LANG(?item2Label)) = "en")
        }
      }
      FILTER(?item2Label = ?maybeGenus)
      BIND(ENCODE_FOR_URI(REPLACE(STR(?item), ".*Q", "Q")) AS ?qid)
      BIND(ENCODE_FOR_URI(REPLACE(STR(?item2), ".*Q", "Q")) AS ?P29)
    }
    """

    tolink = wbi_helpers.execute_sparql_query(query=query, prefix=sparql_prefixes)

    wbi = WikibaseIntegrator(login=login)
    print(f"{str(len(tolink['results']['bindings']))} items to link to parent taxa")

    for i in tolink['results']['bindings']:
        q = wbi.item.get(i['qid']['value'])
        q.claims.add(datatypes.Item(i['P29']['value'], prop_nr="P29"))
        if args.dryrun:
            print(f"DRY RUN: Link {i['qid']['value']} to parent taxon")
        else:
            print(f"Link {i['qid']['value']} to parent taxon")
            q.write(summary="Link host taxon to genus by name")

