#!/usr/bin/env python

# Check for reference statements with a reference DOI (P27) but without a
# "stated in" (P23) link to a reference item.
#
# When editing, references can be added with just a reference DOI (P27) without
# creating a corresponding reference item first. The DOIs can then be used to
# retrieve article titles (from Wikidata) and create reference items.
#
# The reference statements are then linked to the reference items with the same
# DOI value.


import json
import argparse
from pprint import pprint

from wikibaseintegrator import WikibaseIntegrator, datatypes, wbi_helpers
from common import wbi_config, login, sparql_prefixes

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dryrun", action="store_true")
    args = parser.parse_args()

    query_refs = """
    SELECT DISTINCT ?ref ?DOI WHERE {
        ?ref ppt:P13 ?DOI
    }
    """

    all_refs = wbi_helpers.execute_sparql_query(
        query=query_refs, prefix=sparql_prefixes
    )
    doi2ref = {
        i["DOI"]["value"]: i["ref"]["value"].split("/")[-1]
        for i in all_refs["results"]["bindings"]
    }

    query_items_with_unlinked_refs = """
    SELECT DISTINCT ?host ?interaction WHERE {
      ?host pps:P19 ?interaction.
      ?interaction prov:wasDerivedFrom ?refnode.
      ?refnode ppsr:P27 ?doi.
      FILTER NOT EXISTS { ?refnode ppsr:P23 ?statedin }
      BIND (UCASE(STR(?doi)) AS ?DOI)
    }
    """

    unlinked_refs = wbi_helpers.execute_sparql_query(
        query=query_items_with_unlinked_refs, prefix=sparql_prefixes
    )
    wbi = WikibaseIntegrator(login=login)
    items_to_process = list(
        set(
            [
                i["host"]["value"].split("/")[-1]
                for i in unlinked_refs["results"]["bindings"]
            ]
        )
    )  # for testing
    print(f"{len(items_to_process)} items to process")

    for q in items_to_process:
        current_item = wbi.item.get(q)
        for interaction in current_item.claims.get("P19"):
            counter = 0
            for current_ref in interaction.references:
                if (
                    len(current_ref.snaks.get("P23")) == 0
                    and len(current_ref.snaks.get("P27")) == 1
                ):  # no stated in and only one doi
                    # print(doi)
                    doi = current_ref.snaks.get("P27")[0].datavalue["value"].upper()
                    if doi in doi2ref:
                        current_ref.add(datatypes.Item(doi2ref[doi], prop_nr="P23"))
                        counter += 1
        if args.dryrun:
            print(
                f"DRY RUN: Link items in {str(counter)} reference statements for item {q}"
            )
        else:
            print(f"Link items in {str(counter)} reference statements for item {q}")
            current_item.write(summary="link items to reference statements by DOI")
