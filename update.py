import requests
import db
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from datetime import date
from common_functions import (
    update_availability,
    update_github_info,
    update_version,
    get_doi_pmid_source,
    add_years,
)
from wos import impacts

Session = sessionmaker(bind=db.engine)
session = Session()


def update_tool_types(tool_types, id):
    types_from_db = select(db.tool_types).where(db.tool_types.bio_id == id)

    for type in session.scalars(types_from_db):
        if type.name not in tool_types:
            print("Deleting type: " + type.name)
            session.delete(type)

    for type in tool_types:
        if (
            not session.query(db.tool_types)
            .filter(db.tool_types.bio_id == id, db.tool_types.name == type)
            .first()
        ):
            print("Adding type: " + type)
            new_type = db.tool_types(bio_id=id, name=type)
            session.add(new_type)
    session.commit()


def update_institutes(institutes, id):
    institutes_set = set()
    for i in institutes:
        if i["typeEntity"] == "Institute":
            institutes_set.add(i["name"])
    institutes_list = list(institutes_set)

    institutes_from_db = select(db.institutes).where(db.institutes.bio_id == id)
    for institute in session.scalars(institutes_from_db):
        if institute.name not in institutes_list:
            print("Deleting institute: " + institute.name)
            session.delete(institute)

    for institute in institutes_list:
        if (
            not session.query(db.institutes)
            .filter(db.institutes.bio_id == id, db.institutes.name == institute)
            .first()
        ):
            print("Adding institute " + institute)
            new_institute = db.institutes(bio_id=id, name=institute)
            session.add(new_institute)
    session.commit()


def update_topics(topics, id):
    topic_term = []
    topic_uri = []
    for t in topics:
        if t["term"] not in topic_term:
            topic_term.append(t["term"])
            topic_uri.append(t["uri"])

    topics_from_db = select(db.topics).where(db.topics.bio_id == id)
    for topic in session.scalars(topics_from_db):
        if topic.term not in topic_term:
            print("Deleting topic: " + topic.term)
            session.delete(topic)

    for i, term in enumerate(topic_term):
        if (
            not session.query(db.topics)
            .filter(db.topics.bio_id == id, db.topics.term == term)
            .first()
        ):
            print("Adding topic: " + term)
            new_topic = db.topics(bio_id=id, term=term, uri=topic_uri[i])
            session.add(new_topic)
    session.commit()


def update_functions(functions, id):
    if not functions:
        return
    function_term = []
    function_uri = []
    for f in functions[0]["operation"]:
        function_term.append(f["term"])
        function_uri.append(f["uri"])

    functions_from_db = select(db.functions).where(db.functions.bio_id == id)
    for function in session.scalars(functions_from_db):
        if function.term not in function_term:
            print("Deleting function: " + function.term)
            session.delete(function)

    for i, term in enumerate(function_term):
        if (
            not session.query(db.functions)
            .filter(db.functions.bio_id == id, db.functions.term == term)
            .first()
        ):
            print("Adding function: " + term)
            new_function = db.functions(bio_id=id, term=term, uri=function_uri[i])
            session.add(new_function)
    session.commit()


def update_platforms(platforms, id):
    platforms_from_db = select(db.platforms).where(db.platforms.bio_id == id)
    for platform in session.scalars(platforms_from_db):
        if platform.name not in platforms:
            print("Deleting platform: " + platform.name)
            session.delete(platform)
    for platform in platforms:
        if (
            not session.query(db.platforms)
            .filter(db.platforms.bio_id == id, db.platforms.name == platform)
            .first()
        ):
            print("Adding platform: " + platform)
            new_platform = db.platforms(bio_id=id, name=platform)
            session.add(new_platform)
    session.commit()


def update_input_output(functions, id, input_or_outut, table):
    if not functions:
        return
    items = []
    for f in functions[0][input_or_outut]:
        items.append(f["data"]["term"])
    items_from_db = select(table).where(table.bio_id == id)
    for item in session.scalars(items_from_db):
        if item.term not in items:
            print("Deleting input/output: " + item.term)
            session.delete(item)
    for item in items:
        if (
            not session.query(table)
            .filter(table.bio_id == id, table.term == item)
            .first()
        ):
            print("Adding input/output: " + item)
            new_item = table(bio_id=id, term=item)
            session.add(new_item)
    session.commit()


def update_collection_ids(collection_ids, id):
    collection_ids_from_db = select(db.collection_ids).where(
        db.collection_ids.bio_id == id
    )
    for collection_id in session.scalars(collection_ids_from_db):
        if collection_id.coll_id not in collection_ids:
            print("Deleting collection_id: " + collection_id.coll_id)
            session.delete(collection_id)
    for collection_id in collection_ids:
        if (
            not session.query(db.collection_ids)
            .filter(
                db.collection_ids.bio_id == id,
                db.collection_ids.coll_id == collection_id,
            )
            .first()
        ):
            print("Adding collection_id: " + collection_id)
            new_collection_id = db.collection_ids(bio_id=id, coll_id=collection_id)
            session.add(new_collection_id)
    session.commit()


def update_elixir_platforms_nodes_communities(items, id, table):
    items_from_db = select(table).where(table.bio_id == id)
    for item in session.scalars(items_from_db):
        if item.name not in items:
            print(f"Deleting {item.name} from {table}")
            session.delete(item)
    for item in items:
        if (
            not session.query(table)
            .filter(table.bio_id == id, table.name == item)
            .first()
        ):
            print(f"Adding {item} to {table}")
            new_item = table(bio_id=id, name=item)
            session.add(new_item)
    session.commit()


def update_years(doi, pmid):
    response = requests.get(
        f"https://www.ebi.ac.uk/europepmc/webservices/rest/MED/{pmid}/citations/1/1000/json"
    ).json()
    citation_count = response["hitCount"]
    if citation_count < 1:
        return 0
    number_of_pages = (response["hitCount"] // 1000) + 1
    year_2022 = 0
    for i in range(1, number_of_pages + 1):
        response = requests.get(
            f"https://www.ebi.ac.uk/europepmc/webservices/rest/MED/{pmid}/citations/{i}/1000/json"
        ).json()
        for item in response["citationList"]["citation"]:
            year = str(item["pubYear"])
            if year == "2022":
                year_2022 += 1
    year_2022_from_db = select(db.years).where(
        db.years.doi == doi, db.years.year == "2022"
    )
    for year in session.scalars(year_2022_from_db):
        print(f"Year 2022 citations before: {year.count} and after: {year_2022}")
        year.count = str(year_2022)
    session.commit()
    return citation_count


def update_publications_and_years(publications, id):
    citation_count = 0
    impact_factor = 0
    journals = set()
    for publication in publications:
        pub_doi = "" if not publication["doi"] else publication["doi"].lower()
        pmid = publication["pmid"]
        pmcid = publication["pmcid"]
        pub_doi, pmid, source = get_doi_pmid_source(pub_doi, pmid, pmcid)
        if (
            not session.query(db.publications)
            .filter(db.publications.bio_id == id, db.publications.doi == pub_doi)
            .first()
        ):
            print("Adding brand new publication: " + pub_doi)
            citations_source = ""
            if pmid:
                citations_source = (
                    f"https://europepmc.org/search?query=CITES%3A{pmid}_{source}"
                )
                citation_count += add_years(pub_doi, pmid, session, db)
            journal = (
                ""
                if not publication["metadata"]
                else publication["metadata"]["journal"]
            )
            if journal:
                journals.add(journal)
            impact = 0 if journal.upper() not in impacts else impacts[journal.upper()]
            impact_factor += impact
            new_publication = db.publications(
                doi=pub_doi,
                bio_id=id,
                pmid=pmid,
                pmcid=pmcid,
                citations_source=citations_source,
                impact_factor=impact_factor,
                journal=journal,
                citation_count=citation_count,
            )
            session.add(new_publication)
            continue
        publication_from_db = select(db.publications).where(
            db.publications.bio_id == id, db.publications.doi == pub_doi
        )
        for pub in session.scalars(publication_from_db):
            citation_count += update_years(pub.doi, pub.pmid)
            pub.citation_count = citation_count
            journals.add(pub.journal)
            impact_factor += pub.impact_factor
    session.commit()
    return citation_count, round(impact_factor, 3), ", ".join(list(journals))


def update_tools():
    tools_from_db = select(db.tools)
    for tool in session.scalars(tools_from_db):
        response = requests.get(
            f'https://bio.tools/api/tool/?&biotoolsID="{tool.bio_id}"&format=json'
        ).json()
        response_list = response["list"][0]
        id = response_list["biotoolsID"]
        print("PROCESSING TOOL " + id)
        tool.name = response_list["name"]
        tool.description = response_list["description"]
        tool.homepage = response_list["homepage"]
        tool.version = update_version(response_list["version"])
        update_tool_types(response_list["toolType"], id)
        update_institutes(response_list["credit"], id)
        update_topics(response_list["topic"], id)
        update_functions(response_list["function"], id)
        tool.maturity = response_list["maturity"]
        update_platforms(response_list["operatingSystem"], id)
        update_input_output(response_list["function"], id, "input", db.inputs)
        update_input_output(response_list["function"], id, "output", db.outputs)
        tool.license = response_list["license"]
        tool.availability = update_availability(id)
        tool.documentation = (
            response_list["documentation"][0]["url"]
            if response_list["documentation"]
            else ""
        )
        update_collection_ids(response_list["collectionID"], id)
        update_elixir_platforms_nodes_communities(
            response_list["elixirPlatform"], id, db.elixir_platforms
        )
        update_elixir_platforms_nodes_communities(
            response_list["elixirNode"], id, db.elixir_nodes
        )
        update_elixir_platforms_nodes_communities(
            response_list["elixirCommunity"], id, db.elixir_communities
        )
        (
            tool.citation_count,
            tool.impact_factor,
            tool.journals,
        ) = update_publications_and_years(response_list["publication"], id)
        (
            tool.url,
            tool.created_at,
            tool.updated_at,
            tool.forks,
            tool.contributions,
        ) = update_github_info(response_list["link"])
        tool.last_updated = date.today()
    session.commit()


update_tools()
