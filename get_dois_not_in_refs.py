import json
import argparse
from common import wbi_config, login, sparql_prefixes
from wikibaseintegrator import WikibaseIntegrator, datatypes, wbi_helpers

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get DOIs not represented in reference items; use output to import new references to Wikiadta with SourceMD"
    )
    parser.add_argument("--dryrun", action="store_true")
    args = parser.parse_args()

    query = """
    SELECT DISTINCT ?DOI 
    WHERE {
      ?host pps:P19 ?interaction.
      ?interaction prov:wasDerivedFrom ?refnode.
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
    """

    recs = wbi_helpers.execute_sparql_query(query=query, prefix=sparql_prefixes)

    for i in recs["results"]["bindings"]:
        print(i["DOI"]["value"])
