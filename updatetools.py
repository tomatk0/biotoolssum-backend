import requests
import common.db as db
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import math
from common.common_functions import update_version, update_availability, update_github_info, get_years_for_graphs, create_options_for_graphs, create_display_string, get_tools_from_db
from datetime import date, datetime
from common.wos import impacts
from flaskapp import add_tool
import json

Session = sessionmaker(bind=db.engine)

def update_tooltypes(tooltypes, id):
    tooltypes = list(set(tooltypes))
    with Session() as session:
        tooltypes_db = session.scalars(select(db.tool_types).where(db.tool_types.bio_id == id))
        for type in tooltypes_db:
            if type.name in tooltypes:
                tooltypes.remove(type.name)
            else:
                print(f"DELETING TOOLTYPE: {type.name}")
                session.delete(type)
        for type in tooltypes:
            print(f'ADDING NEW TOOLTYPE {type}')
            session.add(db.tool_types(bio_id=id, name=type))
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN UPDATE TOOLTYPES {repr(e)}')
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
                print(f'DELETING INSTITUTE {institute.name}')
                session.delete(institute)
        for institute in institutes:
            print(f'ADDING NEW INSTITUTE {institute}')
            session.add(db.institutes(bio_id=id, name=institute))
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN UPDATE INSTITUTES {repr(e)}')
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
                print(f'DELETING TOPIC {topic.term}')
                session.delete(topic)
        for key, value in topics_dict.items():
            print(f'ADDING NEW TOPIC {key}')
            session.add(db.topics(bio_id=id, term=key, uri=value))
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN UPDATE TOPICS {repr(e)}')
            session.rollback()

def update_operations(function_id, items):
    operations_dict = {}
    for item in items:
        operations_dict[item['term']] = item['uri']
    with Session() as session:
        operations_db = session.scalars(select(db.operations).where(db.operations.function_id == function_id))
        for op in operations_db:
            if op.term in operations_dict:
                operations_dict.pop(op.term)
            else:
                print(f'DELETING OPERATION {op.term}')
                session.delete(op)
        for key, value in operations_dict.items():
            print(f'ADDING A BRAND NEW OPERATION {key} FOR FUNCTION {function_id}')
            session.add(db.operations(function_id=function_id, term=key, uri=value))
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN UPDATE OPERATIONS {repr(e)}')

def update_inputs(function_id, items):
    inputs_set = set()
    for item in items:
        inputs_set.add(item['data']['term'])
    inputs_list = list(inputs_set)
    with Session() as session:
        inputs_db = session.scalars(select(db.inputs).where(db.inputs.function_id == function_id))
        for i in inputs_db:
            if i.term in inputs_list:
                inputs_list.remove(i.term)
            else:
                print(f'DELETING INPUT {i.term}')
                session.delete(i)
        for i in inputs_list:
            print(f'ADDING A BRAND NEW INPUT {i} FOR FUNCTION {function_id}')
            session.add(db.inputs(function_id=function_id, term=i))
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN UPDATE INPUTS {repr(e)}')

def update_outputs(function_id, items):
    outputs_set = set()
    for item in items:
        outputs_set.add(item['data']['term'])
    outputs_list = list(outputs_set)
    with Session() as session:
        outputs_db = session.scalars(select(db.outputs).where(db.outputs.function_id == function_id))
        for i in outputs_db:
            if i.term in outputs_list:
                outputs_list.remove(i.term)
            else:
                print(f'DELETING OUTPUT {i.term}')
                session.delete(i)
        for i in outputs_list:
            print(f'ADDING A BRAND NEW OUTPUT {i} FOR FUNCTION {function_id}')
            session.add(db.inputs(function_id=function_id, term=i))
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN UPDATE OUTPUTS {repr(e)}')

def update_functions(items, id):
    if not items:
        return True
    items_dict = {}
    for i, item in enumerate(items):
        func_id = f'{id}_{i+1}'
        items_dict[func_id] = item
    with Session() as session:
        for key, value in items_dict.items():
            update_operations(key, value['operation'])
            update_inputs(key, value['input'])
            update_outputs(key, value['output'])
            if not session.scalars(select(db.functions).where(db.functions.function_id == key)).first():
                session.add(db.functions(function_id=key, bio_id=id))
                print(f'ADDING A BRAND NEW FUNCTION {key}')
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN UPDATE FUNCTIONS {repr(e)}')

def update_documentations(documentations, id):
    if not documentations:
        return
    documentations_dict = {}
    for d in documentations:
        doc_url = d['url']
        if not doc_url or doc_url in documentations_dict:
            continue
        documentations_dict[doc_url] = d['type']
    with Session() as session:
        documentations_db = session.scalars(select(db.documentations).where(db.documentations.bio_id == id))
        for documentation in documentations_db:
            if documentation.url in documentations_dict:
                documentations_dict.pop(documentation.url)
            else:
                print(f'DELETING DOCUMENTATION {documentations.url}')
                session.delete(documentation)
        for key, value in documentations_dict.items():
            print(f'ADDING NEW DOCUMENTATION {key}')
            session.add(db.documentations(bio_id=id, url=doc_url, type=value))
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN UPDATE DOCUMENTATIONS {repr(e)}')
            session.rollback()

def update_platforms(platforms, id):
    platforms = list(set(platforms))
    with Session() as session:
        platforms_db = session.scalars(select(db.platforms).where(db.platforms.bio_id == id))
        for platform in platforms_db:
            if platform.name in platforms:
                platforms.remove(platform.name)
            else:
                print(f'DELETING PLATFORMS {platform.name}')
                session.delete(platform)
        for platform in platforms:
            print(f'ADDING NEW PLATFORM {platform}')
            session.add(db.platforms(bio_id=id, name=platform))
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN UPDATE PLATFORMS {repr(e)}')
            session.rollback()

def update_collection_ids(collection_ids, id):
    collection_ids = list(set(collection_ids))
    with Session() as session:
        collection_ids_db = session.scalars(select(db.collection_ids).where(db.collection_ids.bio_id == id))
        for collection_id in collection_ids_db:
            if collection_id.coll_id in collection_ids:
                collection_ids.remove(collection_id.coll_id)
            else:
                print(f'DELETING COLLECTION ID {collection_id.coll_id}')
                session.delete(collection_id)
        for collection_id in collection_ids:
            print(f'ADDING NEW COLLECTION ID {collection_id}')
            session.add(db.collection_ids(bio_id = id, coll_id = collection_id))
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN UPDATE COLLECTION IDS {repr(e)}')
            session.rollback()

def update_elixir_platforms_nodes_communities(items, id, table):
    items = list(set(items))
    with Session() as session:
        items_db = session.scalars(select(table).where(table.bio_id == id))
        for item in items_db:
            if item.name in items:
                items.remove(item.name)
            else:
                print(f'DELETING {item.name} FROM {table}')
                session.delete(item)
        for item in items:
            session.add(table(bio_id = id, name=item))
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN ELIXIR {repr(e)}')
            session.rollback()

def update_publications_and_years(publications, id):
    tool_citations_count = 0
    used_doi = []
    years_for_graphs = {}
    with Session() as session:
        for publication in publications:
            doi = '' if 'doi' not in publication or not publication['doi'] else publication['doi'].lower()
            pmid = '' if 'pmid' not in publication or not publication['pmid'] else publication['pmid']
            response = requests.get(f"https://badge.dimensions.ai/details/doi/{doi}/metadata.json?domain=https://bio.tools")
            if doi:
                response = requests.get(f"https://badge.dimensions.ai/details/doi/{doi}/metadata.json?domain=https://bio.tools")
            elif pmid:
                response = requests.get(f"https://badge.dimensions.ai/details/pmid/{pmid}/metadata.json?domain=https://bio.tools")
            else:
                print(f'NOT DOI NOR PMID')
                continue
            if not response.ok:
                continue
            if not response.json():
                if not doi:
                    continue
                if doi not in used_doi:
                    print(f'CREATING PUBLICATION WITH DOI ONLY doi: {doi} bio_id: {id} pmid: {pmid}')
                    session.add(db.publications(bio_id=id, doi=doi, pmid=pmid))
                    used_doi.append(doi)
                    continue
            response = response.json()
            doi = doi if 'doi' not in response else response['doi']
            if not doi or doi in used_doi:
                print(f"PUB DOI MISSING {id} OR DUPLICATE DOI")
                continue
            used_doi.append(doi)
            pub_citations_count = 0 if 'times_cited' not in response else response['times_cited']
            tool_citations_count += pub_citations_count
            journal = '' if 'journal' not in response or 'title' not in response['journal'] else response['journal']['title']
            impact = 0
            if journal:
                impact = 0 if journal.upper() not in impacts else impacts[journal.upper()]
            existing_publication = session.scalars(select(db.publications).where(db.publications.bio_id == id, db.publications.doi == doi)).first()
            if existing_publication:
                print(f'UPDATING PUBLICATION {doi}, CITATIONS COUNT BEFORE: {existing_publication.citations_count} AFTER: {pub_citations_count}')
                existing_publication.citations_count = pub_citations_count
                years_for_graphs[existing_publication.title] = get_years_for_graphs(existing_publication.doi)
                continue
            badge_dimensions_id = '' if 'id' not in response else response['id']
            citations_source = f"https://badge.dimensions.ai/details/id/{badge_dimensions_id}/citations"
            authors = '' if 'author_names' not in response else response['author_names']
            date = '' if 'date' not in response else response['date']
            pmid = '' if 'pmid' not in response else response['pmid']
            title = '' if 'title' not in response else response['title']
            years_for_graphs[title] = get_years_for_graphs(doi)
            print(f"ADDING NEW PUBLICATION {doi}")
            session.add(db.publications(doi=doi, bio_id=id, pmid=pmid, title=title, authors=authors, journal=journal, impact=round(impact, 3), publication_date=date, citations_count=pub_citations_count, citations_source=citations_source))
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN UPDATE PUBLICATIONS AND YEARS {repr(e)}')
            session.rollback()
        return tool_citations_count, years_for_graphs

def add_queries_matrix_data_cycle(id):
    matrix_queries = ['dna sequence', 'dna secondary structure', 'dna structure', 'genomics', 'rna sequence', 'rna secondary structure', 'rna structure', 'rna omics', 'protein sequence', 'protein secondary structure', 'protein structure', 'protein omics', 'small molecule primary sequence', 'small molecule secondary structure', 'small molecule structure', 'small molecule omics']
    data_cycle_queries = ['acquisition', 'data processing', 'analysis', 'storage', 'share', 'data management', 'fair']
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
        for query in data_cycle_queries:
            if bool(session.query(db.data_cycle_queries).filter_by(bio_id=id, data_cycle_query=query).first()):
                continue
            response = requests.get(f'https://bio.tools/api/tool/?page=1&q={query}&biotoolsID=\"{id}\"&format=json')
            if not response.ok:
                return
            response = response.json()
            if response['count'] < 1:
                continue
            session.add(db.data_cycle_queries(bio_id=id, data_cycle_query=query))
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN MATRIX QUERIES {repr(e)}')
            session.rollback()

def check_for_broken_tool(id):
    tables = [db.tool_types, db.institutes, db.topics, db.platforms, db.collection_ids, db.documentations, db.elixir_communities, db.elixir_nodes, db.elixir_platforms, db.publications, db.matrix_queries, db.data_cycle_queries]
    with Session() as session:
        for func in session.scalars(select(db.functions).where(db.functions.bio_id == id)):
            function_id = func.function_id
            for o in session.scalars(select(db.operations).where(db.operations.function_id == function_id)):
                session.delete(o)
            for i in session.scalars(select(db.inputs).where(db.inputs.function_id == function_id)):
                session.delete(i)
            for o in session.scalars(select(db.outputs).where(db.outputs.function_id == function_id)):
                session.delete(o)
            session.delete(func)
        for table in tables:
            for item in session.scalars(select(table).where(table.bio_id == id)):
                session.delete(item)
        session.commit()
        
def update_tool(item, id):
    with Session() as session:
        tool = session.scalars(select(db.tools).where(db.tools.bio_id == id)).first()
        if not tool:
            check_for_broken_tool(id)
            print(f"ADDING A BRAND NEW TOOL {id}")
            tool = add_tool(item, id)
            if tool:
                try:
                    session.add(tool)
                    session.commit()
                    add_queries_matrix_data_cycle(id)
                except Exception as e:
                    print(f"ROLLBACK IN ADDING A NEW TOOL {id} {repr(e)}")
                    session.rollback()
            return
        tool_last_update = datetime.strptime(tool.last_updated, "%m/%d/%Y")
        if (tool_last_update.day == date.today().day):
            print(f'TOOL {id} HAS BEEN UPDATED TODAY ALREADY')
            return
        print(f'UPDATING TOOL {id}')
        tool.name = item["name"]
        tool.homepage = item["homepage"]
        tool.description = item["description"]
        tool.maturity = item["maturity"]
        tool.license = item["license"]
        tool.version = update_version(item["version"])
        tool.availability = update_availability(id)
        tool.github_url, tool.github_created_at, tool.github_updated_at, tool.github_forks, tool.github_contributions, tool.github_stars = update_github_info(item['link'])
        tool.last_updated = (date.today()).strftime("%m/%d/%Y")
        tool.citation_count, years_for_graphs = update_publications_and_years(item['publication'], id)
        tool.options_for_graph = create_options_for_graphs(tool.name, years_for_graphs)
        update_tooltypes(item["toolType"], id)
        update_institutes(item['credit'], id)
        update_topics(item['topic'], id)
        update_functions(item['function'], id)
        update_platforms(item['operatingSystem'], id)
        update_collection_ids(item['collectionID'], id)
        update_elixir_platforms_nodes_communities(item['elixirPlatform'], id, db.elixir_platforms)
        update_elixir_platforms_nodes_communities(item['elixirNode'], id, db.elixir_nodes)
        update_elixir_platforms_nodes_communities(item['elixirCommunity'], id, db.elixir_communities)
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN UPDATE TOOLS {repr(e)}')
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

def update_json(query_id):
    with Session() as session:
        query = session.scalars(select(db.queries).where(db.queries.id == query_id)).first()
        result, matrix_tools, matrix_tools_sizes, data_cycle_tools, data_cycle_tools_sizes = get_tools_from_db(query.collection_id, query.topic, query.tools_list)
        print(f'TOOLS FROM DB: {len(result)}')
        resulting_string = create_display_string(query.collection_id, query.topic)
        data = {"resulting_string": resulting_string, "data": result, "matrix_tools": matrix_tools, "matrix_tools_sizes": matrix_tools_sizes, "data_cycle_tools": data_cycle_tools, "data_cycle_tools_sizes": data_cycle_tools_sizes}
        json_data = json.dumps(data)
        query.data = json_data.encode()
        try:
            print('UPDATING JSON')
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN UPDATING JSON {repr(e)}')
            session.rollback()

def update_tools_from_api(coll_id, topic, tools_list, query_id):
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
    update_json(query_id)

def update_tools():
    with Session() as session:
        print(f'DATE OF UPDATE {date.today()}')
        queries = session.scalars(select(db.queries))
        for q in queries:
            print('----------------------------------------------------------------------------------------------------------------------------------------------------------------------')
            print(f"CURRENTLY UPDATING QUERY {q.id}")
            update_tools_from_api(q.collection_id, q.topic, q.tools_list, q.id)

update_tools()