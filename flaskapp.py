from flask import Flask, session, render_template, jsonify, request
import requests
import db
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import math
from flask_cors import CORS, cross_origin
import random
from wos import impacts
from datetime import date
from common_functions import update_availability, update_github_info, update_version, get_doi_pmid_source, add_years
from time import time

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app)

Session = sessionmaker(bind=db.engine)
session = Session()

def add_tool_types(tool_types, bio_id):
    already_used = []
    for name in tool_types:
        if name in already_used:
            continue
        already_used.append(name)
        new_tool_type = db.tool_types(bio_id=bio_id, name=name)
        session.add(new_tool_type)
    try:
        session.commit()
    except:
        session.rollback()
    
def add_institutes(credit, bio_id):
    for item in credit:
        if item['typeEntity'] == 'Institute':
            name = item['name']
            new_institute = db.institutes(bio_id=bio_id, name=name)
            session.add(new_institute)
    try:
        session.commit()
    except:
        session.rollback()

def add_topics(topics, bio_id):
    already_used = []
    for item in topics:
        term = item['term']
        uri = item['uri']
        if term in already_used:
            continue
        already_used.append(term)
        new_topic = db.topics(bio_id=bio_id, term=term, uri=uri)
        session.add(new_topic)
    try:
        session.commit()
    except:
        session.rollback()

def add_functions(functions, bio_id):
    if not functions:
        return
    already_used = []
    for item in functions[0]['operation']:
        term = item['term']
        uri = item['uri']
        if term in already_used:
            continue
        already_used.append(term)
        new_function = db.functions(bio_id=bio_id, term=term, uri=uri)
        session.add(new_function)
    try:
        session.commit()
    except:
        session.rollback()

def add_platforms(platforms, bio_id):
    for name in platforms:
        new_platform = db.platforms(bio_id=bio_id, name=name)
        session.add(new_platform)
    try:
        session.commit()
    except:
        session.rollback()

def add_input_output(functions, bio_id, input_or_output, table):
    if not functions:
        return
    already_used = []
    for item in functions[0][input_or_output]:
        term = item['data']['term']
        if term in already_used:
            continue
        already_used.append(term)
        new_item = table(bio_id=bio_id, term=term)
        session.add(new_item)
    try:
        session.commit()
    except:
        session.rollback()

def add_collection_ids(collection_ids, bio_id):
    already_used = []
    for coll_id in collection_ids:
        if coll_id in already_used:
            continue
        already_used.append(coll_id)
        new_coll_id = db.collection_ids(bio_id=bio_id, coll_id=coll_id)
        session.add(new_coll_id)
    try:
        session.commit()
    except:
        session.rollback()

def add_elixir_platforms_nodes_communities(items, bio_id, table):
    if not items:
        return
    already_used = []
    for item in items:
        if item in already_used:
            continue
        already_used.append(item)
        new_item = table(bio_id=bio_id, name=item)
        session.add(new_item)
    try:
        session.commit()
    except:
        session.rollback()

def add_publications_and_years(publications, bio_id):
    min_year, max_year = '2022', '2022'
    citation_count = 0
    impact_factor = 0
    journals = set()
    for publication in publications:
        pub_doi = '' if not publication['doi'] else publication['doi'].lower()
        pmid = publication['pmid']
        pmcid = publication['pmcid']
        pub_doi, pmid, source = get_doi_pmid_source(pub_doi, pmid, pmcid)
        if not pub_doi:
            print(f"PUB DOI MISSING {bio_id}")
            continue
        if bool(session.query(db.publications).filter_by(doi=pub_doi, bio_id=bio_id, pmid=pmid).first()):
            print(f"PUBLICATION ALREADY IN DB FROM OTHER TOOL {pub_doi}")
            continue
        citations_source = ''
        if pmid:
            citations_source = f'https://europepmc.org/search?query=CITES%3A{pmid}_{source}'
            cit_count, min_y, max_y = add_years(pub_doi, pmid, session, db)
            citation_count += cit_count
            if min_y < min_year:
                min_year = min_y
            if max_y > max_year:
                max_year = max_y
        journal = '' if not publication['metadata'] else publication['metadata']['journal']
        if journal:
            journals.add(journal)
        impact = 0 if journal.upper() not in impacts else impacts[journal.upper()]
        impact_factor += impact         
        new_publication = db.publications(doi=pub_doi, bio_id=bio_id, pmid=pmid, pmcid=pmcid, citations_source=citations_source, impact_factor=impact_factor, journal=journal, citation_count=citation_count)
        session.add(new_publication)
    try:
        session.commit()
    except:
        session.rollback()
    return citation_count, round(impact_factor, 3), ', '.join(list(journals)), min_year, max_year

def add_tool(item, id):
    name = item['name']
    version = update_version(item['version'])
    bio_link = f'https://bio.tools/{id}'
    homepage = item['homepage']
    add_tool_types(item['toolType'], id)
    add_institutes(item['credit'], id)
    description = item['description']
    add_topics(item['topic'], id)
    add_functions(item['function'], id)
    maturity = item['maturity']
    add_platforms(item['operatingSystem'], id)
    add_input_output(item['function'], id, 'input', db.inputs)
    add_input_output(item['function'], id, 'output', db.outputs)
    license = item['license']
    availability = update_availability(id)
    documentation = item['documentation'][0]['url'] if item['documentation'] else ''
    add_collection_ids(item['collectionID'], id)
    add_elixir_platforms_nodes_communities(item['elixirPlatform'], id, db.elixir_platforms)
    add_elixir_platforms_nodes_communities(item['elixirNode'], id, db.elixir_nodes)
    add_elixir_platforms_nodes_communities(item['elixirCommunity'], id, db.elixir_communities)
    citation_count, impact_factor, journals, min_year, max_year = add_publications_and_years(item['publication'], id)
    url, created_at, updated_at, forks, contributions = update_github_info(item['link'])
    last_updated = date.today()
    tool = db.tools(bio_id=id, name=name, version=version, bio_link=bio_link, homepage=homepage, description=description, maturity=maturity, license=license, citation_count=citation_count,impact_factor=impact_factor,journals=journals, availability = availability, documentation=documentation, github_url=url, github_created_at=created_at, github_updated_at=updated_at, github_forks=forks, github_contributions=contributions, last_updated=last_updated, min_year=min_year, max_year=max_year)
    return tool
        
def get_publications_and_years_from_table(tool):
    publications_list = []
    publications = select(db.publications).where(db.publications.bio_id == tool.bio_id)
    for publication in session.scalars(publications):
        citations_list = []
        years = select(db.years).where(db.years.doi == publication.doi)
        for year in session.scalars(years):
            citations_list.append(year.serialize())
        publication.citations_list = citations_list
        publications_list.append(publication.serialize())
    return publications_list

def get_data_from_table(tool, table):
    result = []
    query = select(table).where(table.bio_id == tool.bio_id)
    for item in session.scalars(query):
        result.append(item.serialize())
    return result

def get_lists_for_tool(tool):
    tool.matrix_queries = get_data_from_table(tool, db.matrix_queries)
    tool.publications = get_publications_and_years_from_table(tool)
    tool.functions = get_data_from_table(tool, db.functions)
    tool.topics = get_data_from_table(tool, db.topics)
    tool.institutes = get_data_from_table(tool, db.institutes)
    tool.platforms = get_data_from_table(tool, db.platforms)
    tool.tool_types = get_data_from_table(tool, db.tool_types)
    tool.inputs = get_data_from_table(tool, db.inputs)
    tool.outputs = get_data_from_table(tool, db.outputs)
    tool.collection_ids = get_data_from_table(tool, db.collection_ids)
    tool.elixir_platforms = get_data_from_table(tool, db.elixir_platforms)
    tool.elixir_nodes = get_data_from_table(tool, db.elixir_nodes)
    tool.elixir_communities = get_data_from_table(tool, db.elixir_communities)

def get_tools_from_given_list(tools_list):
    result = []
    for t in tools_list.split(','):
            response = requests.get(f'https://bio.tools/api/tool/?&biotoolsID=\"{t}\"&format=json').json()
            if not response['list']:
                continue
            item = response['list'][0]
            id = item['biotoolsID']
            print(f'Processing {id} from API (list)')
            if bool(session.query(db.tools).filter_by(bio_id=id).first()):
                continue
            tool = add_tool(item, id)
            if tool:
                session.add(tool)
                get_lists_for_tool(tool)
                result.append(tool.serialize())
    try:
        session.commit()
    except:
        session.rollback()
    return result

def get_tools_from_api(coll_id, topic, tools_list, count_db):
    result = []
    if tools_list:
        return get_tools_from_given_list(tools_list)
    response = requests.get(f'https://bio.tools/api/tool/?{coll_id}{topic}&format=json').json()
    count_api = response['count'] - count_db
    if count_api == 0:
        return result
    count = math.ceil(response['count'] / 10) + 1
    for i in range(1, count):
        response = requests.get(f'https://bio.tools/api/tool/?page={i}{coll_id}{topic}&format=json').json()
        for item in response['list']:
            id = item['biotoolsID']
            print(f'Processing {id} from API')
            if bool(session.query(db.tools).filter_by(bio_id=id).first()):
                continue
            tool = add_tool(item, id)
            if tool:
                session.add(tool)
                get_lists_for_tool(tool)
                result.append(tool.serialize())
    try:
        session.commit()
    except:
        session.rollback()
    return result

def get_tools_from_db(coll_id, topic, tools_list):
    result = []
    query = select(db.tools).where(db.tools.bio_id == db.collection_ids.bio_id, db.collection_ids.coll_id.ilike(coll_id))
    if topic:
        query = select(db.tools).where(db.tools.bio_id == db.topics.bio_id, db.topics.term.ilike(topic))
    elif tools_list:
        for tool in tools_list.split(','):
            tool_select = select(db.tools).where(db.tools.bio_id == tool)
            for t in session.scalars(tool_select):
                print(f'Processing {t.bio_id} from DB (list)')
                get_lists_for_tool(t)
                result.append(t.serialize())
        return result
    for tool in session.scalars(query):
        print(f'Processing {tool.bio_id} from DB')
        get_lists_for_tool(tool)
        result.append(tool.serialize())
    return result

def show_only_names(tools, only_names):
    if only_names == 'off':
        return tools
    result = []
    for tool in tools:
        tool_select = select(db.tools).where(db.tools.bio_id == tool['bio_id'])
        for t in session.scalars(tool_select):
            result.append(t.serialize_name_only())
    return result

def get_existing_queries():
    result = []
    queries_select = select(db.queries)
    for query in session.scalars(queries_select):
        result.append(query.serialize())
    return result

def create_hash():
    result = ''
    for _ in range(10):
        result += chr(random.randint(48, 122))
    return result

@app.route("/", methods=["POST", "GET"])
def get_parameters():
    existing_queries = get_existing_queries() 
    if request.method == "POST":
        non_empty = 0
        coll_id_form = request.form.get("coll_id")
        topic_form = request.form.get("topic")
        tools_list_form = request.form.get("tools_list")
        for item in [coll_id_form, topic_form, tools_list_form]:
            if item:
                non_empty += 1
        if non_empty != 1:
            return render_template("get_parameters.html")
        only_names_form = 'off' if not request.form.get('only_names') else 'on'
        display_type = request.form.get('option')
        if bool(session.query(db.queries).filter_by(collection_id=coll_id_form, topic=topic_form, tools_list=tools_list_form, display_type=display_type, only_names=only_names_form).first()):
            return render_template("get_parameters.html", content=existing_queries)  
        _ = get_tools(coll_id_form, topic_form, tools_list_form, only_names_form, display_type)
        new_query = db.queries(id=create_hash(), collection_id=coll_id_form, topic=topic_form, tools_list=tools_list_form, display_type=display_type, only_names=only_names_form)
        session.add(new_query)
        try:
            session.commit()
        except:
            session.rollback()
        existing_queries = get_existing_queries()
        return render_template("get_parameters.html", content=existing_queries)   
    return render_template("get_parameters.html", content=existing_queries)

@app.route("/data", methods=["POST"])
@cross_origin()
def get_data_from_frontend():
    if request.method == "POST":
        request_data = request.get_json()
        id = request_data['id']
        query_select = select(db.queries).where(db.queries.id == id)
        query = None
        for q in session.scalars(query_select):
            query = q
        return get_tools(query.collection_id, query.topic, query.tools_list, query.only_names, query.display_type)

def add_matrix_queries(coll_id, topic):
    matrix_queries = ['dna sequence', 'dna secondary structure', 'dna structure', 'genomics', 'rna sequence', 'rna secondary structure', 'rna structure', 'rna omics', 'protein sequence', 'protein secondary structure', 'protein structure', 'protein omics', 'small molecule primary sequence', 'small molecule secondary structure', 'small molecule structure', 'small molecule omics']
    coll_or_topic = f'&collectionID=\"{coll_id}\"' if coll_id else f'&topic=\"{topic}\"'
    for query in matrix_queries:
        page = "?page=1"
        while page:
            response = requests.get(f'https://bio.tools/api/tool/{page}&q={query}{coll_or_topic}&format=json').json()
            tools = response['list']
            for tool in tools:
                id = tool['biotoolsID']
                if bool(session.query(db.matrix_queries).filter_by(bio_id=id, matrix_query=query).first()):
                    continue
                new_query = db.matrix_queries(bio_id=id, matrix_query=query)
                session.add(new_query)
            page = response['next']
    try:
        session.commit()
    except:
        session.rollback()
          
def get_tools(coll_id, topic, tools_list, only_names, display_type):
    result_db = get_tools_from_db(coll_id, topic, tools_list)
    count_db = len(result_db)
    print(f'TOOLS FROM DB:{count_db}')
    coll_id = f'&collectionID=\"{coll_id}\"' if coll_id else ''
    topic = f'&topic=\"{topic}\"' if topic else ''
    result_api = get_tools_from_api(coll_id, topic, tools_list, count_db)
    print(f'TOOLS FROM API:{len(result_api)}')
    add_matrix_queries(coll_id, topic)
    result_db.extend(result_api)
    result = show_only_names(result_db, only_names)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
