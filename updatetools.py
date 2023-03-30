import requests
import common.db as db
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import math
from common.common_functions import update_version, update_availability, update_github_info, get_doi_pmid_source_details_citation_count
from datetime import date
from common.wos import impacts
from flaskapp import add_years, add_tool
import logging

Session = sessionmaker(bind=db.engine)

def update_tooltypes(tooltypes, id):
    tooltypes = list(set(tooltypes))
    with Session() as session:
        tooltypes_db = session.scalars(select(db.tool_types).where(db.tool_types.bio_id == id))
        for type in tooltypes_db:
            if type.name in tooltypes:
                tooltypes.remove(type.name)
            else:
                logging.info(f"DELETING TOOLTYPE: {type.name}")
                session.delete(type)
        for type in tooltypes:
            logging.info(f'ADDING NEW TOOLTYPE {type}')
            session.add(db.tool_types(bio_id=id, name=type))
        try:
            session.commit()
        except Exception as e:
            logging.info(f'ROLLING BACK IN UPDATE TOOLTYPES {repr(e)}')
            session.rollback()
            
def update_institutes(institutes, id):
    institutes_set = set()
    for i in institutes:
        if i["typeEntity"] == "Institute":
            institutes_set.add(i["name"])
    institutes = list(institutes_set)

    with Session() as session:
        institutes_db = session.scalars(select(db.institutes).where(db.institutes.bio_id == id))
        for institute in institutes_db:
            if institute.name in institutes:
                institutes.remove(institute.name)
            else:
                logging.info(f'DELETING INSTITUTE {institute.name}')
                session.delete(institute)
        for institute in institutes:
            logging.info(f'ADDING NEW INSTITUTE {institute}')
            session.add(db.institutes(bio_id=id, name=institute))
        try:
            session.commit()
        except Exception as e:
            logging.info(f'ROLLING BACK IN UPDATE INSTITUTES {repr(e)}')
            session.rollback()

def update_topics(topics, id):
    topics_dict = {}
    for t in topics:
        term = t['term']
        if not term or term in topics_dict:
            continue
        topics_dict[term] = t["uri"]

    with Session() as session:
        topics_db = session.scalars(select(db.topics).where(db.topics.bio_id == id))
        for topic in topics_db:
            if topic.term in topics_dict:
                topics_dict.pop(topic.term)
            else:
                logging.info(f'DELETING TOPIC {topic.term}')
                session.delete(topic)
        for key, value in topics_dict.items():
            logging.info(f'ADDING NEW TOPIC {key}')
            session.add(db.topics(bio_id=id, term=key, uri=value))
        try:
            session.commit()
        except Exception as e:
            logging.info(f'ROLLING BACK IN UPDATE TOPICS {repr(e)}')
            session.rollback()


def update_functions(functions, id):
    if not functions:
        return
    functions_dict = {}
    for f in functions[0]['operation']:
        term = f['term']
        if not term or term in functions_dict:
            continue
        functions_dict[term] = f["uri"]

    with Session() as session:
        functions_db = session.scalars(select(db.functions).where(db.functions.bio_id == id))
        for function in functions_db:
            if function.term in functions_dict:
                functions_dict.pop(function.term)
            else:
                logging.info(f'DELETING FUNCTION {functions.term}')
                session.delete(function)
        for key, value in functions_dict.items():
            logging.info(f'ADDING NEW FUNCTION {key}')
            session.add(db.functions(bio_id=id, term=key, uri=value))
        try:
            session.commit()
        except Exception as e:
            logging.info(f'ROLLING BACK IN UPDATE FUNCTIONS {repr(e)}')
            session.rollback()

def update_platforms(platforms, id):
    platforms = list(set(platforms))
    with Session() as session:
        platforms_db = session.scalars(select(db.platforms).where(db.platforms.bio_id == id))
        for platform in platforms_db:
            if platform.name in platforms:
                platforms.remove(platform.name)
            else:
                logging.info(f'DELETING PLATFORMS {platform.name}')
                session.delete(platform)
        for platform in platforms:
            logging.info(f'ADDING NEW PLATFORM {platform}')
            session.add(db.platforms(bio_id=id, name=platform))
        try:
            session.commit()
        except Exception as e:
            logging.info(f'ROLLING BACK IN UPDATE PLATFORMS {repr(e)}')
            session.rollback()

def update_input_output(functions, id, input_or_output, table):
    if not functions:
        return
    items = []
    for f in functions[0][input_or_output]:
        term = f["data"]["term"]
        if not term or term in items:
            continue
        items.append(term)
    with Session() as session:
        items_db = session.scalars(select(table).where(table.bio_id == id))
        for item in items_db:
            if item.term in items:
                items.remove(item.term)
            else:
                logging.info(f'DELETING INPUT/OUTPUT {item.term}')
                session.delete(item)
        for item in items:
            logging.info(f'ADDING NEW INPUT/OUTPUT {item}')
            session.add(table(bio_id=id, term=item))
        try:
            session.commit()
        except Exception as e:
            logging.info(f'ROLLING BACK IN UPDATE I/O {repr(e)}')
            session.rollback()

def update_collection_ids(collection_ids, id):
    collection_ids = list(set(collection_ids))
    with Session() as session:
        collection_ids_db = session.scalars(select(db.collection_ids).where(db.collection_ids.bio_id == id))
        for collection_id in collection_ids_db:
            if collection_id.coll_id in collection_ids:
                collection_ids.remove(collection_id.coll_id)
            else:
                logging.info(f'DELETING COLLECTION ID {collection_id.coll_id}')
                session.delete(collection_id)
        for collection_id in collection_ids:
            logging.info(f'ADDING NEW COLLECTION ID {collection_id}')
            session.add(db.collection_ids(bio_id = id, coll_id = collection_id))
        try:
            session.commit()
        except Exception as e:
            logging.info(f'ROLLING BACK IN UPDATE COLLECTION IDS {repr(e)}')
            session.rollback()

def update_elixir_platforms_nodes_communities(items, id, table):
    items = list(set(items))
    with Session() as session:
        items_db = session.scalars(select(table).where(table.bio_id == id))
        for item in items_db:
            if item.name in items:
                items.remove(item.name)
            else:
                logging.info(f'DELETING {item.name} FROM {table}')
                session.delete(item)
        for item in items:
            session.add(table(bio_id = id, name=item))
        try:
            session.commit()
        except Exception as e:
            logging.info(f'ROLLING BACK IN ELIXIR {repr(e)}')
            session.rollback()

def update_years(doi, pmid):
    response = requests.get(
        f"https://www.ebi.ac.uk/europepmc/webservices/rest/MED/{pmid}/citations/1/1000/json"
    )
    if not response.ok:
        return 0, False
    response = response.json()
    citation_count = response['hitCount']
    if citation_count < 1:
        return 0, False
    number_of_pages = (response["hitCount"] // 1000) + 1
    year_2023 = 0
    for i in range(1, number_of_pages + 1):
        response = requests.get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/MED/{pmid}/citations/{i}/1000/json") 
        if not response.ok:
            return 0, False
        response = response.json()
        for item in response["citationList"]["citation"]:
            year = str(item["pubYear"])
            if year == "2023":
                year_2023 += 1
    with Session() as session:
        year_2023_db = session.scalars(select(db.years).where(db.years.doi == doi, db.years.year == "2023")).first()
        if year_2023_db:
            logging.info(f'YEAR 2023 CITATIONS BEFORE: {year_2023_db.count} AND AFTER: {year_2023}')
            year_2023_db.count = str(year_2023)
        try:
            session.commit()
        except Exception as e:
            logging.info(f'ROLLING BACK IN UPDATE YEARS {repr(e)}')
            session.rollback()
    if year_2023 > 0:
        return citation_count, True
    return citation_count, False


def update_publications_and_years(publications, id):
    min_year, max_year = None, None
    citation_count = 0
    impact_factor = 0
    journals = set()
    used_doi = []
    with Session() as session:
        for publication in publications:
            pub_doi = '' if not publication['doi'] else publication['doi'].lower()
            pmid = publication['pmid']
            pmcid = publication['pmcid']
            pub_doi, pmid, source, details = get_doi_pmid_source_details_citation_count(pub_doi, pmid, pmcid)
            if not pub_doi or pub_doi in used_doi:
                logging.info(f"PUB DOI MISSING {id} OR DUPLICATE DOI")
                continue
            used_doi.append(pub_doi)
            existing_publication = session.scalars(select(db.publications).where(db.publications.bio_id == id, db.publications.doi == pub_doi)).first()
            if existing_publication:
                logging.info(f'UPDATING PUBLICATION {pub_doi}')
                if pmid:
                    cit_count, result = update_years(pub_doi, pmid)
                    citation_count += cit_count
                    if result:
                        max_year = '2023'
                continue
            if pmid:
                citations_source = f'https://europepmc.org/search?query=CITES%3A{pmid}_{source}'
                cit_count, min_y, max_y = add_years(pub_doi, pmid)
                citation_count += cit_count
                if not min_year and min_y:
                    min_year = min_y
                if not max_year and max_y:
                    max_year = max_y
                if min_y and min_y < min_year:
                    min_year = min_y
                if max_y and max_y > max_year:
                    max_year = max_y
            journal = '' if not publication['metadata'] else publication['metadata']['journal']
            if journal:
                journals.add(journal)
                impact = 0 if journal.upper() not in impacts else impacts[journal.upper()]
                impact_factor += impact
            citations_source = ''
            logging.info(f"ADDING NEW PUBLICATION {pub_doi}")
            session.add(db.publications(doi=pub_doi, bio_id=id, pmid=pmid, pmcid=pmcid, details=details, citations_source=citations_source))
        tool = session.scalars(select(db.tools).where(db.tools.bio_id == id)).first()
        if tool:
            logging.info(f"OLD CITATION COUNT: {tool.citation_count} NEW CITATION COUNT: {citation_count}")
            if max_year != '2023':
                max_year = tool.max_year
        try:
            session.commit()
        except Exception as e:
            logging.info(f'ROLLING BACK IN UPDATE PUBLICATIONS AND YEARS {repr(e)}')
            session.rollback()
        return citation_count, round(impact_factor, 3), ', '.join(list(journals)), max_year, min_year

def add_matrix_queries(id):
    matrix_queries = ['dna sequence', 'dna secondary structure', 'dna structure', 'genomics', 'rna sequence', 'rna secondary structure', 'rna structure', 'rna omics', 'protein sequence', 'protein secondary structure', 'protein structure', 'protein omics', 'small molecule primary sequence', 'small molecule secondary structure', 'small molecule structure', 'small molecule omics']
    with Session() as session:
        for query in matrix_queries:
            if bool(session.query(db.matrix_queries).filter_by(bio_id=id, matrix_query=query).first()):
                continue
            response = requests.get(f'https://bio.tools/api/tool/?page=1&q={query}&biotoolsID=\"{id}\"&format=json')
            if not response.ok:
                return
            response = response.json()
            if response['count'] < 1:
                continue
            session.add(db.matrix_queries(bio_id=id, matrix_query=query))
        try:
            session.commit()
        except Exception as e:
            logging.info(f'ROLLING BACK IN MATRIX QUERIES {repr(e)}')
            session.rollback()

def update_tool(item, id):
    with Session() as session:
        tool = session.scalars(select(db.tools).where(db.tools.bio_id == id)).first()
        if not tool:
            logging.info(f"ADDING A BRAND NEW TOOL {id}")
            tool = add_tool(item, id)
            if tool:
                try:
                    session.add(tool)
                    session.commit()
                    add_matrix_queries(id)
                except:
                    logging.info(f"ROLLBACK IN ADDING A NEW TOOL {id}")
                    session.rollback()
            return
        logging.info(f'UPDATING TOOL {id}')
        tool.name = item["name"]
        tool.bio_link = f'https://bio.tools/{id}'
        tool.homepage = item["homepage"]
        tool.description = item["description"]
        tool.maturity = item["maturity"]
        tool.license = item["license"]
        tool.documentation = item['documentation'][0]['url'] if item['documentation'] else ''
        tool.version = update_version(item["version"])
        tool.availability = update_availability(id)
        tool.github_url, tool.github_created_at, tool.github_updated_at, tool.github_forks, tool.github_contributions = update_github_info(item['link'])
        tool.last_updated = (date.today()).strftime("%m/%d/%Y")
        tool.citation_count, tool.impact_factor, tool.journals, tool.max_year, tool.min_year = update_publications_and_years(item['publication'], id)
        update_tooltypes(item["toolType"], id)
        update_institutes(item['credit'], id)
        update_topics(item['topic'], id)
        update_functions(item['function'], id)
        update_platforms(item['operatingSystem'], id)
        update_input_output(item['function'], id, "input", db.inputs)
        update_input_output(item['function'], id, "output", db.outputs)
        update_collection_ids(item['collectionID'], id)
        update_elixir_platforms_nodes_communities(item['elixirPlatform'], id, db.elixir_platforms)
        update_elixir_platforms_nodes_communities(item['elixirNode'], id, db.elixir_nodes)
        update_elixir_platforms_nodes_communities(item['elixirCommunity'], id, db.elixir_communities)
        try:
            session.commit()
        except Exception as e:
            logging.info(f'ROLLING BACK IN UPDATE TOOLS {repr(e)}')
            session.rollback()

def update_tools_from_given_list(tools_list):
    split_list = tools_list.split(',')
    if not split_list or split_list[0] == '':
        return
    for t in split_list:
        response = requests.get(f'https://bio.tools/api/tool/?&biotoolsID=\"{t}\"&format=json')
        if not response.ok:
            return
        response = response.json()
        if not response['list']:
            continue
        item = response['list'][0]
        id = item['biotoolsID']
        update_tool(item, id)


def update_tools_from_api(coll_id, topic, tools_list):
    coll_id = f'&collectionID=\"{coll_id}\"' if coll_id else ''
    topic = f'&topic=\"{topic}\"' if topic else ''
    if not coll_id and not topic:
        update_tools_from_given_list(tools_list)
        return
    response = requests.get(f'https://bio.tools/api/tool/?{coll_id}{topic}&format=json')
    if not response.ok:
        return
    response = response.json()
    count = math.ceil(response['count'] / 10) + 1
    for i in range(1, count):
        response = requests.get(f'https://bio.tools/api/tool/?page={i}{coll_id}{topic}&format=json')
        if not response.ok:
            return
        response = response.json()
        for item in response['list']:
            id = item['biotoolsID']
            update_tool(item, id)


def update_tools():
    logging.basicConfig(filename="logfiles/updatetools.log", level=logging.INFO, format="%(asctime)s %(message)s")
    with Session() as session:
        queries = session.scalars(select(db.queries))
        for q in queries:
            logging.info(f"CURRENTLY UPDATING QUERY {q.id}")
            update_tools_from_api(q.collection_id, q.topic, q.tools_list)

update_tools()