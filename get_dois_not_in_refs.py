#!/usr/bin/env python3

import json
import argparse
from common import wbi_config, login, sparql_prefixes
from wikibaseintegrator import WikibaseIntegrator, datatypes, wbi_helpers

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get DOIs not represented in reference items; use output to import new references to Wikiadta with SourceMD or Scholia"
    )
    parser.add_argument("--dryrun", action="store_true")
    parser.add_argument("--claim", type=str, default="P19", help="""P19 - interaction; P36 - environmental material; P38 - environmental system; P40 - local environmental context; P41 - interacts experimentally with; P28 - representative sequence for placeholder taxon; P34 - representative SSU rRNA sequence record""")
    args = parser.parse_args()

    allowed_claims = ["P19", "P36", "P38", "P40", "P41", "P28", "P34"]
    if args.claim in allowed_claims:
        item_class = args.claim
    else:
        print(f"Unrecognized property identifier {args.claim}, please specify one of {' '.join(allowed_claims)}")
        exit()

    query = """
    SELECT DISTINCT ?DOI 
    WHERE {
      ?host pps:%s ?statement.
      ?statement prov:wasDerivedFrom ?refnode.
      ?refnode ppsr:P27 ?doi.
      # check that no reference item already linked in this statement
      FILTER NOT EXISTS { ?refnode ppsr:P23 ?statedin }
      # wikidata standardizes DOI in uppercase
      BIND (UCASE(STR(?doi)) AS ?DOI)
      # check that no reference with this DOI already exists
      FILTER NOT EXISTS {
        ?ref ppt:P18 pp:Q3;
             ppt:P13 ?DOI. 
      }
    }
    """ % (item_class)

    recs = wbi_helpers.execute_sparql_query(query=query, prefix=sparql_prefixes)

    for i in recs["results"]["bindings"]:
        print(i["DOI"]["value"])
