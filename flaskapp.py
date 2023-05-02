from flask import Flask, render_template, jsonify, request
import requests
import common.db as db
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import math
from flask_cors import CORS, cross_origin
import random
from common.wos import impacts
from datetime import date
from common.common_functions import update_availability, update_github_info, update_version, get_years_for_graphs, create_options_for_graphs, create_display_string, get_tools_from_db
from celery import Celery
import json

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['CORS_HEADERS'] = 'Content-Type'
app.app_context().push()
cors = CORS(app)

Session = sessionmaker(bind=db.engine, autoflush=False)
celery = Celery(app.name, broker='amqp://myuser:mypassword@localhost:5672/myvhost', backend='db+mysql+pymysql://biotoolsDB:password@localhost/brokerDB')

def create_session_commit_data(data, location):
    with Session() as session:
        try:
            session.add_all(data)
            session.commit()
            return True
        except Exception as e:
            print(f'ROLLING BACK IN {location} {repr(e)}')
            session.rollback()
            return False

def add_tool_types(tool_types, bio_id):
    tool_types = list(set(tool_types))
    result = []
    for name in tool_types:
        if not name:
            continue
        result.append(db.tool_types(bio_id=bio_id, name=name))
    return create_session_commit_data(result, 'ADD TOOL TYPES')
    
def add_institutes(credit, bio_id):
    result = []
    for item in credit:
        name = item['name']
        if name and item['typeEntity'] == 'Institute':
            result.append(db.institutes(bio_id=bio_id, name=name))
    return create_session_commit_data(result, 'ADD INSTITUTES')

def add_topics(topics, bio_id):
    already_used = []
    result = []
    for item in topics:
        term = item['term']
        uri = item['uri']
        if not term or term in already_used:
            continue
        already_used.append(term)
        result.append(db.topics(bio_id=bio_id, term=term, uri=uri))
    return create_session_commit_data(result, 'ADD TOPICS')

def add_functions(items, bio_id):
    if not items:
        return True
    functions = []
    operations = []
    inputs = []
    outputs = []
    for i, item in enumerate(items):
        id = f'{bio_id}_{i+1}'
        functions.append(db.functions(function_id=id, bio_id=bio_id))
        already_used = []
        for o in item['operation']:
            term = o['term']
            if not term or term in already_used:
                continue
            operations.append(db.operations(function_id=id, term=term, uri=o['uri']))
            already_used.append(term)
        already_used = []
        for input in item['input']:
            term = input['data']['term']
            if not term or term in already_used:
                continue
            inputs.append(db.inputs(function_id=id, term=term))
            already_used.append(term)
        already_used = []
        for output in item['output']:
            term = output['data']['term']
            if not term or term in already_used:
                continue
            outputs.append(db.outputs(function_id=id, term=term))
            already_used.append(term)
    return create_session_commit_data(functions, 'ADD FUNCTIONS') and create_session_commit_data(operations, 'ADD OPERATIONS') and create_session_commit_data(inputs, 'ADD INPUTS') and create_session_commit_data(outputs, 'ADD OUTPUTS')

def add_platforms(platforms, bio_id):
    platforms = list(set(platforms))
    result = []
    for name in platforms:
        if name:
            result.append(db.platforms(bio_id=bio_id, name=name))
    return create_session_commit_data(result, 'ADD PLATFORMS')

# def add_input_output(functions, bio_id, input_or_output, table):
#     if not functions:
#         return True
#     already_used = []
#     result = []
#     for item in functions[0][input_or_output]:
#         term = item['data']['term']
#         if not term or term in already_used:
#             continue
#         already_used.append(term)
#         result.append(table(bio_id=bio_id, term=term))
#     return create_session_commit_data(result, input_or_output)

def add_collection_ids(collection_ids, bio_id):
    collection_ids = list(set(collection_ids))
    result = []
    for coll_id in collection_ids:
        if not coll_id:
            continue
        result.append(db.collection_ids(bio_id=bio_id, coll_id=coll_id))
    return create_session_commit_data(result, 'ADD COLLECTION IDS')

def add_documentations(documentations, bio_id):
    if not documentations:
        return True
    already_used = []
    result = []
    for item in documentations:
        url = item['url']
        doc_type = item['type']
        if url in already_used:
            continue
        already_used.append(url)
        result.append(db.documentations(bio_id=bio_id, url=url, type=doc_type[0]))
    return create_session_commit_data(result, 'ADD DOCUMENTATIONS')

def add_elixir_platforms_nodes_communities(items, bio_id, table):
    if not items:
        return  True
    items = list(set(items))
    result = []
    for item in items:
        if not item:
            continue
        new_item = table(bio_id=bio_id, name=item)
        result.append(new_item)
    return create_session_commit_data(result, 'ADD ELIXIR')

def add_publications_and_years(publications, bio_id):
    tool_citations_count = 0
    used_doi = []
    publications_result = []
    years_for_graphs = {}
    try:
        for publication in publications:
            doi = '' if 'doi' not in publication or not publication['doi'] else publication['doi'].lower()
            pmid = '' if 'pmid' not in publication or not publication['pmid'] else publication['pmid']
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
                print(f'CREATING PUBLICATION WITH DOI ONLY doi: {doi} bio_id: {bio_id}')
                new_publication = db.publications(doi=doi, bio_id=bio_id)
                publications_result.append(new_publication)
                continue
            response = response.json()
            doi = doi if 'doi' not in response else response['doi']
            if not doi or doi in used_doi:
                print(f'DOI MISSING {bio_id} OR DUPLICATE DOI')
                continue
            used_doi.append(doi)
            badge_dimensions_id = '' if 'id' not in response else response['id']
            citations_source = f"https://badge.dimensions.ai/details/id/{badge_dimensions_id}/citations"
            authors = '' if 'author_names' not in response else response['author_names']
            date = '' if 'date' not in response else response['date']
            journal = '' if 'journal' not in response or 'title' not in response['journal'] else response['journal']['title']
            impact = 0
            if journal:
                impact = 0 if journal.upper() not in impacts else impacts[journal.upper()]
            pmid = '' if 'pmid' not in response else response['pmid']
            pub_citations_count = 0 if 'times_cited' not in response else response['times_cited']
            tool_citations_count += pub_citations_count
            title = '' if 'title' not in response else response['title']
            years_for_graphs[title] = get_years_for_graphs(doi)
            publications_result.append(db.publications(doi=doi, bio_id=bio_id, pmid=pmid, title=title, authors=authors, journal=journal, impact=round(impact, 3), publication_date=date, citations_count=pub_citations_count, citations_source=citations_source))
        return tool_citations_count, publications_result, years_for_graphs
    except Exception as e:
        print(f'ERROR IN ADD PUBLICATIONS AND YEARS {repr(e)}')
        return 0, None, None

def add_tool(item, id):
    if not add_tool_types(item['toolType'], id):
        return None
    if not add_institutes(item['credit'], id):
        return None
    if not add_topics(item['topic'], id):
        return None
    if not add_functions(item['function'], id):
        return None
    if not add_platforms(item['operatingSystem'], id):
        return None
    if not add_collection_ids(item['collectionID'], id):
        return None
    if not add_documentations(item['documentation'], id):
        return None
    if not add_elixir_platforms_nodes_communities(item['elixirPlatform'], id, db.elixir_platforms):
        return None
    if not add_elixir_platforms_nodes_communities(item['elixirNode'], id, db.elixir_nodes):
        return None
    if not add_elixir_platforms_nodes_communities(item['elixirCommunity'], id, db.elixir_communities):
        return None
    citation_count, publications_result, years_for_graphs = add_publications_and_years(item['publication'], id)
    if not create_session_commit_data(publications_result, 'PUBLICATIONS'):
        return None
    name = item['name']
    options_for_graph = create_options_for_graphs(name, years_for_graphs)
    version = update_version(item['version'])
    bio_link = f'https://bio.tools/{id}'
    homepage = item['homepage']
    description = item['description']
    maturity = item['maturity']
    license = item['license']
    availability = update_availability(id)
    url, created_at, updated_at, forks, contributions, stars = update_github_info(item['link'])
    last_updated = (date.today()).strftime("%m/%d/%Y")
    tool = db.tools(bio_id=id, name=name, version=version, bio_link=bio_link, homepage=homepage, description=description, maturity=maturity, license=license, citation_count=citation_count, availability = availability, github_url=url, github_created_at=created_at, github_updated_at=updated_at, github_forks=forks, github_contributions=contributions, github_stars=stars, last_updated=last_updated, options_for_graph=options_for_graph)
    return tool

def get_tools_from_given_list(tools_list):
    split_list = tools_list.replace(' ', '').split(',')
    if not split_list or split_list[0] == '':
        return
    total = 0
    with Session() as session:
        for t in split_list:
                response = requests.get(f'https://bio.tools/api/tool/?&biotoolsID=\"{t}\"&format=json')
                if not response.ok:
                    return
                response = response.json()
                if not response['list']:
                    continue
                item = response['list'][0]
                id = item['biotoolsID']
                print(f'Processing {id} from API (list)')
                tool = add_tool(item, id)
                if tool:
                    session.add(tool)
                    total += 1
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN GET TOOLS FROM GIVEN LIST {repr(e)}')
            session.rollback()
    print(f'TOOLS FROM API {total}')
    if total > 0:
        add_queries_matrix_data_cycle_list(tools_list)
        query_id = create_new_query('', '', tools_list)
        create_new_json(query_id)  

@celery.task(ignore_result=True)
def get_tools_from_api(coll_id, topic, tools_list):
    coll_id = f'&collectionID=\"{coll_id}\"' if coll_id else ''
    topic = f'&topic=\"{topic}\"' if topic else ''
    if not coll_id and not topic:
        get_tools_from_given_list(tools_list)
        return
    response = requests.get(f'https://bio.tools/api/tool/?{coll_id}{topic}&format=json')
    if not response.ok:
        return
    response = response.json()
    total = 0
    with Session() as session:
        count = math.ceil(response['count'] / 10) + 1
        for i in range(1, count):
            response = requests.get(f'https://bio.tools/api/tool/?page={i}{coll_id}{topic}&format=json')
            if not response.ok:
                return
            response = response.json()
            for item in response['list']:
                id = item['biotoolsID']
                print(f'Processing {id} from API')
                tool = add_tool(item, id)
                if tool:
                    session.add(tool)
                    total += 1
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN GET TOOLS FROM API {repr(e)}')
            session.rollback()
    print(f'TOOLS FROM API {total}')
    if total > 0:
        add_queries_matrix_data_cycle(coll_id, topic)
        query_id = create_new_query(coll_id, topic, '')
        create_new_json(query_id)   

def create_hash():
    result = ''
    for _ in range(10):
        result += chr(random.randint(48, 91))
    return result

@app.route("/", methods=["POST", "GET"])
def get_parameters():
    if request.method == "POST":
        coll_id_form = request.form.get("coll_id")
        topic_form = request.form.get("topic")
        tools_list_form = request.form.get("tools_list")
        if not coll_id_form and not topic_form and not tools_list_form:
            return render_template("get_parameters.html", error="Fill collection id or topic or create a list.")
        if coll_id_form and topic_form or tools_list_form and (coll_id_form or topic_form):
            return render_template("get_parameters.html", error="Either fill out collection id or topic, or create a list.")
        with Session() as session:
            if bool(session.query(db.queries).filter_by(collection_id=coll_id_form, topic=topic_form, tools_list=tools_list_form).first()):
                return render_template("get_parameters.html", error="This query already exists.")
        get_tools_from_api.delay(coll_id_form, topic_form, tools_list_form)
        return render_template("get_parameters.html")   
    return render_template("get_parameters.html")

@app.route("/data", methods=["POST"])
@cross_origin()
def get_data_from_frontend():
    with Session() as session:
        request_data = request.get_json()
        id = request_data['id']
        encoded_json = session.scalars(select(db.finished_jsons).where(db.finished_jsons.id == id)).first()
        if not encoded_json:
            return jsonify(resulting_string="This query is not in the database", data=[])
        json_data = encoded_json.data.decode('utf-8')
    return json.loads(json_data)


@app.route("/get_queries", methods=["GET"])
def get_queries():
    result = []
    queries_select = select(db.queries)
    with Session() as session:
        for query in session.scalars(queries_select):
            result.append(query)
    return render_template("get_queries.html", content=result)

def add_queries_matrix_data_cycle_list(tools_list):
    split_list = tools_list.split(',')
    if split_list[0] == '':
        return
    matrix_queries = ['dna sequence', 'dna secondary structure', 'dna structure', 'genomics', 'rna sequence', 'rna secondary structure', 'rna structure', 'rna omics', 'protein sequence', 'protein secondary structure', 'protein structure', 'protein omics', 'small molecule primary sequence', 'small molecule secondary structure', 'small molecule structure', 'small molecule omics']
    data_cycle_queries = ['acquisition', 'data processing', 'analysis', 'storage', 'share', 'data management', 'fair']
    with Session() as session:
        for item in split_list:
            for query in matrix_queries:
                if bool(session.query(db.matrix_queries).filter_by(bio_id=item, matrix_query=query).first()):
                    continue
                response = requests.get(f'https://bio.tools/api/tool/?page=1&q={query}&biotoolsID=\"{item}\"&format=json')
                if not response.ok:
                    return
                response = response.json()
                if response['count'] < 1:
                    continue
                session.add(db.matrix_queries(bio_id=item, matrix_query=query))
        for item in split_list:
            for query in data_cycle_queries:
                if bool(session.query(db.data_cycle_queries).filter_by(bio_id=item, data_cycle_query=query).first()):
                    continue
                response = requests.get(f'https://bio.tools/api/tool/?page=1&q={query}&biotoolsID=\"{item}\"&format=json')
                if not response.ok:
                    return
                response = response.json()
                if response['count'] < 1:
                    continue
                session.add(db.data_cycle_queries(bio_id=item, data_cycle_query=query))
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN MATRIX QUERIES {repr(e)}')
            session.rollback()
                
def add_queries_matrix_data_cycle(coll_id, topic):
    matrix_queries = ['dna sequence', 'dna secondary structure', 'dna structure', 'genomics', 'rna sequence', 'rna secondary structure', 'rna structure', 'rna omics', 'protein sequence', 'protein secondary structure', 'protein structure', 'protein omics', 'small molecule primary sequence', 'small molecule secondary structure', 'small molecule structure', 'small molecule omics']
    data_cycle_queries = ['acquisition', 'data processing', 'analysis', 'storage', 'share', 'data management', 'fair']
    coll_or_topic = coll_id if coll_id else topic
    with Session() as session:
        for query in matrix_queries:
            page = "?page=1"
            while page:
                response = requests.get(f'https://bio.tools/api/tool/{page}&q={query}{coll_or_topic}&format=json')
                if not response.ok:
                    return
                response = response.json()
                tools = response['list']
                for tool in tools:
                    id = tool['biotoolsID']
                    if bool(session.query(db.matrix_queries).filter_by(bio_id=id, matrix_query=query).first()):
                        continue
                    session.add(db.matrix_queries(bio_id=id, matrix_query=query))
                page = response['next']
        for query in data_cycle_queries:
            page = "?page=1"
            while page:
                response = requests.get(f'https://bio.tools/api/tool/{page}&q={query}{coll_or_topic}&format=json')
                if not response.ok:
                    return
                response = response.json()
                tools = response['list']
                for tool in tools:
                    id = tool['biotoolsID']
                    if bool(session.query(db.data_cycle_queries).filter_by(bio_id=id, data_cycle_query=query).first()):
                        continue
                    session.add(db.data_cycle_queries(bio_id=id, data_cycle_query=query))
                page = response['next']
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN MATRIX QUERIES {repr(e)}')
            session.rollback()

def create_new_query(coll_id, topic, tools_list):
    if coll_id:
        coll_id = coll_id.split('"')[1]
    elif topic:
        topic = topic.split('"')[1]
    with Session() as session:
        query_id = id=create_hash()
        new_query = db.queries(id=query_id, collection_id=coll_id, topic=topic, tools_list=tools_list)
        session.add(new_query)
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN CREATING NEW QUERY {repr(e)}')
            session.rollback()
    return query_id

def create_new_json(query_id):
    with Session() as session:
        query = session.scalars(select(db.queries).where(db.queries.id == query_id)).first()
        result, matrix_tools, matrix_tools_sizes, data_cycle_tools, data_cycle_tools_sizes  = get_tools_from_db(query.collection_id, query.topic, query.tools_list)
        print(f'TOOLS FROM DB: {len(result)}')
        resulting_string = create_display_string(query.collection_id, query.topic)
        data = {"resulting_string": resulting_string, "data": result, "matrix_tools": matrix_tools, "matrix_tools_sizes": matrix_tools_sizes, "data_cycle_tools": data_cycle_tools, "data_cycle_tools_sizes": data_cycle_tools_sizes}
        json_data = json.dumps(data)
        session.add(db.finished_jsons(id=query.id, data=json_data.encode()))
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN CREATING NEW JSON {repr(e)}')
            session.rollback()

if __name__ == "__main__":
    app.run(debug=True)
