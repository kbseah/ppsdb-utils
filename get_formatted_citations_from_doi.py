#!/usr/bin/env python3

import requests
import argparse
from common import wbi_config, login, sparql_prefixes
from wikibaseintegrator import WikibaseIntegrator, datatypes, wbi_helpers
from wikibaseintegrator.models import References, Reference, Qualifiers

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Add formatted citations (property P14) to reference items, obtained from DOI resolver service"""
    )
    parser.add_argument("--dryrun", action="store_true")
    parser.add_argument(
        "--limit", type=int, default=100, help="Number of entries to process"
    )
    parser.add_argument(
        "--style",
        type=str,
        default="the-company-of-biologists",
        help="Citation style; default was chosen because it does not include DOI redundantly or prefix citation with a number.",
    )
    parser.add_argument(
        "--locale", type=str, default="en-US", help="Locale for formatted citation"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not print message for each item updated",
    )
    parser.add_argument(
        "--max_citation_len",
        default=400,
        help="Maximum length of formatted citation string; limit is set by Wikibase configuration",
    )
    args = parser.parse_args()

    wbi = WikibaseIntegrator(login=login)
    # items with a DOI but without formatted citation
    query = """
    SELECT DISTINCT ?item ?doi WHERE {
      ?item ppt:P13 ?doi.
      FILTER NOT EXISTS { ?item ppt:P14 ?citation. }
      ?item rdfs:label ?itemLabel
    }"""
    rec = wbi_helpers.execute_sparql_query(query=query, prefix=sparql_prefixes)
    to_update = []
    if "bindings" in rec["results"] and len(rec["results"]["bindings"]) > 0:
        for item in rec["results"]["bindings"]:
            to_update.append(
                {
                    "qid": item["item"]["value"].split("/")[-1],
                    "doi": item["doi"]["value"],
                }
            )
    count_updated = 0
    for i in to_update[0 : args.limit]:
        # Get formatted citation by content negotiation as described here
        # https://citation.crosscite.org/docs.html instead of using Crossref
        # API because DOIs may be provided by other resolvers like Datacite
        r = requests.get(
            url=f"https://doi.org/{i['doi']}",
            headers={
                "Accept": f"text/x-bibliography; style={args.style}; locale={args.locale}"
            },
        )
        if r.ok:
            try:
                # crossref returns citation text in latin-1 encoding
                citation = r.text.encode("latin_1").decode("utf_8").rstrip()
            except UnicodeEncodeError:
                # in case it actually returns utf-8 in some cases,
                # encoding as latin-1 will find some characters out of range
                citation = r.text.rstrip()
            # replace consecutive whitespace, nonstandard spaces, and newlines
            # with standard space character
            citation = " ".join(citation.split())
            if len(citation) > args.max_citation_len:
                print(
                    f"Citation for {i['doi']} is longer than {str(args.max_citation_len)} characters. Skipping..."
                )
            else:
                item = wbi.item.get(i["qid"])
                item.claims.add(datatypes.String(prop_nr="P14", value=citation))
                count_updated += 1
                if args.dryrun:
                    if not args.quiet:
                        print(
                            f"DRYRUN: Will add formatted citation to {item.id}: {citation}"
                        )
                else:
                    item.write()
                    if not args.quiet:
                        print(f"Added formatted citation to {item.id}: {citation}")
        else:
            print(f"Problem with retrieving formatted citation for doi {i['doi']}")
            print(r.text)
    if args.dryrun:
        print(str(count_updated) + " items will be updated")
    else:
        print(str(count_updated) + " items updated")
