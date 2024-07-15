#!/usr/bin/env python3

import json
import argparse
from common import wbi_config, login, sparql_prefixes
from wikibaseintegrator import WikibaseIntegrator, datatypes, wbi_helpers

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dryrun", action="store_true")
    parser.add_argument("--claim", type=str, default="P19", help="""P19 - interaction; P36 - environmental material; P38 - environmental system; P40 - local environmental context; P41 - interacts experimentally with; P28 - representative sequence for placeholder taxon; P34 - representative SSU rRNA sequence record""")
    args = parser.parse_args()

    allowed_claims = ["P19", "P36", "P38", "P40", "P41", "P28", "P34"]
    if args.claim in allowed_claims:
        item_class = args.claim
    else:
        print(f"Unrecognized property identifier {args.claim}, please specify one of {' '.join(allowed_claims)}")
        exit()


    query = """SELECT DISTINCT ?wdlabel ?DOI ?wdref
    WITH {
      SELECT DISTINCT ?host ?DOI 
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
    } AS %%dois
    WHERE {
      INCLUDE %%dois
      SERVICE <https://query.wikidata.org/sparql> {
        # find wikidata items with this DOI
        ?wdref wdt:P356 ?DOI;
               rdfs:label ?wdlabel.
        FILTER ( LANG(?wdlabel) = "en" )
      }
    }
    """ % (item_class)  # percent sign in SPARQL query is escaped as double-%

    recs = wbi_helpers.execute_sparql_query(query=query, prefix=sparql_prefixes)

    wbi = WikibaseIntegrator(login=login)

    for i in recs["results"]["bindings"]:
        newitem = wbi.item.new()
        newitem.labels.set("en", i["wdlabel"]["value"])
        newitem.aliases.set("en", i["DOI"]["value"])
        newitem.claims.add(datatypes.Item("Q3", prop_nr="P18"))  # instance of reference
        newitem.claims.add(datatypes.String(i["wdref"]["value"], prop_nr="P2"))
        newitem.claims.add(datatypes.String(i["DOI"]["value"], prop_nr="P13"))
        if args.dryrun:
            print(
                f"DRY RUN: Create new reference item for {i['DOI']['value']}    {i['wdlabel']['value']}"
            )
        else:
            print(
                f"Create new reference item for {i['DOI']['value']}    {i['wdlabel']['value']}"
            )
            newitem.write(summary="Create new reference item from DOI in reference statement")
