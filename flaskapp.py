from flask import Flask, render_template, jsonify, request
import requests
import db
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import math
from flask_cors import CORS, cross_origin
import random
from wos import impacts
from datetime import date
from common_functions import update_availability, update_github_info, update_version, get_doi_pmid_source_details_citation_count
import time
from celery import Celery

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
    already_used = []
    result = []
    for name in tool_types:
        if not name or name in already_used:
            continue
        already_used.append(name)
        new_tool_type = db.tool_types(bio_id=bio_id, name=name)
        result.append(new_tool_type)
    return create_session_commit_data(result, 'ADD TOOL TYPES')
    
def add_institutes(credit, bio_id):
    result = []
    for item in credit:
        name = item['name']
        if name and item['typeEntity'] == 'Institute':
            new_institute = db.institutes(bio_id=bio_id, name=name)
            result.append(new_institute)
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
        new_topic = db.topics(bio_id=bio_id, term=term, uri=uri)
        result.append(new_topic)
    return create_session_commit_data(result, 'ADD TOPICS')

def add_functions(functions, bio_id):
    if not functions:
        return True
    already_used = []
    result = []
    for item in functions[0]['operation']:
        term = item['term']
        uri = item['uri']
        if not term or term in already_used:
            continue
        already_used.append(term)
        new_function = db.functions(bio_id=bio_id, term=term, uri=uri)
        result.append(new_function)
    return create_session_commit_data(result, 'ADD FUNCTIONS')

def add_platforms(platforms, bio_id):
    result = []
    for name in platforms:
        if name:
            new_platform = db.platforms(bio_id=bio_id, name=name)
            result.append(new_platform)
    return create_session_commit_data(result, 'ADD PLATFORMS')

def add_input_output(functions, bio_id, input_or_output, table):
    if not functions:
        return True
    already_used = []
    result = []
    for item in functions[0][input_or_output]:
        term = item['data']['term']
        if not term or term in already_used:
            continue
        already_used.append(term)
        new_item = table(bio_id=bio_id, term=term)
        result.append(new_item)
    return create_session_commit_data(result, input_or_output)

def add_collection_ids(collection_ids, bio_id):
    already_used = []
    result = []
    for coll_id in collection_ids:
        if not coll_id or coll_id in already_used:
            continue
        already_used.append(coll_id)
        new_coll_id = db.collection_ids(bio_id=bio_id, coll_id=coll_id)
        result.append(new_coll_id)
    return create_session_commit_data(result, 'ADD COLLECTION IDS')

def add_elixir_platforms_nodes_communities(items, bio_id, table):
    if not items:
        return  True
    already_used = []
    result = []
    for item in items:
        if not item or item in already_used:
            continue
        already_used.append(item)
        new_item = table(bio_id=bio_id, name=item)
        result.append(new_item)
    return create_session_commit_data(result, 'ADD ELIXIR')

def add_years(doi, pmid):
    response = requests.get(
        f"https://www.ebi.ac.uk/europepmc/webservices/rest/MED/{pmid}/citations/1/1000/json"
    )
    if not response.ok:
        return '2022', '2022'
    response = response.json()
    number_of_pages = (response["hitCount"] // 1000) + 1
    years_dict = {}
    for i in range(1, number_of_pages + 1):
        response = requests.get(
            f"https://www.ebi.ac.uk/europepmc/webservices/rest/MED/{pmid}/citations/{i}/1000/json"
        )
        if not response.ok:
            return '2022', '2022'
        response = response.json()
        for item in response["citationList"]["citation"]:
            year = str(item["pubYear"])
            years_dict[year] = years_dict.get(year, 0) + 1
    keys_list = list(years_dict.keys())
    min_year = "2022" if not keys_list else min(keys_list)
    max_year = "2022" if not keys_list else max(keys_list)
    with Session() as session:
        for key, val in years_dict.items():
            if bool(
                session.query(db.years).filter_by(doi=doi, year=key, count=val).first()
            ):
                return min_year, max_year
            new_year = db.years(doi=doi, year=key, count=val)
            session.add(new_year)
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN ADD YEARS pub_doi {doi} {repr(e)}')
            session.rollback()
    return min_year, max_year

def add_publications_and_years(publications, bio_id):
    min_year, max_year = '2022', '2022'
    citation_count = 0
    impact_factor = 0
    journals = set()
    used_doi = []
    publications_result = []
    for publication in publications:
        pub_doi = '' if not publication['doi'] else publication['doi'].lower()
        pmid = publication['pmid']
        pmcid = publication['pmcid']
        pub_doi, pmid, source, details, cit_count = get_doi_pmid_source_details_citation_count(pub_doi, pmid, pmcid)
        if not pub_doi or pub_doi in used_doi:
            print(f"PUB DOI MISSING {bio_id} OR DUPLICATE DOI")
            continue
        used_doi.append(pub_doi)
        citation_count += cit_count
        citations_source = ''
        if pmid:
            citations_source = f'https://europepmc.org/search?query=CITES%3A{pmid}_{source}'
            min_y, max_y = add_years(pub_doi, pmid)
            if min_y < min_year:
                min_year = min_y
            if max_y > max_year:
                max_year = max_y
        journal = '' if not publication['metadata'] else publication['metadata']['journal']
        if journal:
            journals.add(journal)
            impact = 0 if journal.upper() not in impacts else impacts[journal.upper()]
            impact_factor += impact         
        new_publication = db.publications(doi=pub_doi, bio_id=bio_id, pmid=pmid, pmcid=pmcid, details=details, citations_source=citations_source, impact_factor=impact_factor, journal=journal, citation_count=citation_count)
        publications_result.append(new_publication)
    return citation_count, round(impact_factor, 3), ', '.join(list(journals)), min_year, max_year, publications_result

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
    if not add_input_output(item['function'], id, 'input', db.inputs):
        return None
    if not add_input_output(item['function'], id, 'output', db.outputs):
        return None
    if not add_collection_ids(item['collectionID'], id):
        return None
    if not add_elixir_platforms_nodes_communities(item['elixirPlatform'], id, db.elixir_platforms):
        return None
    if not add_elixir_platforms_nodes_communities(item['elixirNode'], id, db.elixir_nodes):
        return None
    if not add_elixir_platforms_nodes_communities(item['elixirCommunity'], id, db.elixir_communities):
        return None
    citation_count, impact_factor, journals, min_year, max_year, publications_result = add_publications_and_years(item['publication'], id)
    if not create_session_commit_data(publications_result, 'PUBLICATIONS'):
        return None
    name = item['name']
    version = update_version(item['version'])
    bio_link = f'https://bio.tools/{id}'
    homepage = item['homepage']
    description = item['description']
    maturity = item['maturity']
    license = item['license']
    availability = update_availability(id)
    documentation = item['documentation'][0]['url'] if item['documentation'] else ''
    url, created_at, updated_at, forks, contributions = update_github_info(item['link'])
    last_updated = date.today()
    tool = db.tools(bio_id=id, name=name, version=version, bio_link=bio_link, homepage=homepage, description=description, maturity=maturity, license=license, citation_count=citation_count,impact_factor=impact_factor,journals=journals, availability = availability, documentation=documentation, github_url=url, github_created_at=created_at, github_updated_at=updated_at, github_forks=forks, github_contributions=contributions, last_updated=last_updated, min_year=min_year, max_year=max_year)
    return tool
        
def get_publications_and_years_from_table(tool):
    with Session() as session:
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
    with Session() as session:
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
    split_list = tools_list.split(',')
    if not split_list or split_list[0] == '':
        return
    total = 0
    with Session() as session:
        for t in split_list:
                response = requests.get(f'https://bio.tools/api/tool/?&biotoolsID=\"{t}\"&format=json')
                if not response.ok:
                    return total
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
        add_matrix_queries_tools_list(tools_list)
        create_new_query('', '', tools_list)

@celery.task(ignore_result=True)
def get_tools_from_api(coll_id, topic, tools_list):
    coll_id = f'&collectionID=\"{coll_id}\"' if coll_id else ''
    topic = f'&topic=\"{topic}\"' if topic else ''
    if not coll_id and not topic:
        get_tools_from_given_list(tools_list)
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
                return total
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
        add_matrix_queries(coll_id, topic)
        create_new_query(coll_id, topic, '')

def modify_tools_list(found_tools, tools_list):
    new_tools_list = ''
    for item in tools_list.split(','):
        if item not in found_tools:
            new_tools_list += (item + ',')
    return new_tools_list[:-1]

def get_tools_from_db(coll_id, topic, tools_list):
    result = []
    if tools_list:
        with Session() as session:
            found_tools = []
            for tool in tools_list.split(','):
                tool_select = select(db.tools).where(db.tools.bio_id == tool)
                for t in session.scalars(tool_select):
                    found_tools.append(tool)
                    print(f'Processing {t.bio_id} from DB (list)')
                    get_lists_for_tool(t)
                    result.append(t.serialize())
            print(f'TOOLS FROM DB: {len(result)}')
            return result, modify_tools_list(found_tools, tools_list)
    with Session() as session:
        query = select(db.tools).where(db.tools.bio_id == db.collection_ids.bio_id, db.collection_ids.coll_id.ilike(f'%{coll_id}%'))
        if topic:
            query = select(db.tools).where(db.tools.bio_id == db.topics.bio_id, db.topics.term.ilike(f'%{topic}%'))
        for tool in session.scalars(query):
            print(f'Processing {tool.bio_id} from DB')
            get_lists_for_tool(tool)
            result.append(tool.serialize())
        print(f'TOOLS FROM DB: {len(result)}')
        return result, tools_list

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
        query_select = select(db.queries).where(db.queries.id == id)
        query = session.scalars(query_select).first()
        result, _ = get_tools_from_db(query.collection_id, query.topic, query.tools_list)
    return jsonify(resulting_string=create_display_string(query.collection_id, query.topic), data=result) 


@app.route("/get_queries", methods=["GET"])
def get_queries():
    result = []
    queries_select = select(db.queries)
    with Session() as session:
        for query in session.scalars(queries_select):
            result.append(query)
    return render_template("get_queries.html", content=result)

def add_matrix_queries_tools_list(tools_list):
    split_list = tools_list.split(',')
    if split_list[0] == '':
        return
    matrix_queries = ['dna sequence', 'dna secondary structure', 'dna structure', 'genomics', 'rna sequence', 'rna secondary structure', 'rna structure', 'rna omics', 'protein sequence', 'protein secondary structure', 'protein structure', 'protein omics', 'small molecule primary sequence', 'small molecule secondary structure', 'small molecule structure', 'small molecule omics']
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
                new_query = db.matrix_queries(bio_id=item, matrix_query=query)
                session.add(new_query)
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN MATRIX QUERIES {repr(e)}')
            session.rollback()
                
def add_matrix_queries(coll_id, topic):
    matrix_queries = ['dna sequence', 'dna secondary structure', 'dna structure', 'genomics', 'rna sequence', 'rna secondary structure', 'rna structure', 'rna omics', 'protein sequence', 'protein secondary structure', 'protein structure', 'protein omics', 'small molecule primary sequence', 'small molecule secondary structure', 'small molecule structure', 'small molecule omics']
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
                    new_query = db.matrix_queries(bio_id=id, matrix_query=query)
                    session.add(new_query)
                page = response['next']
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN MATRIX QUERIES {repr(e)}')
            session.rollback()

def create_display_string(coll_id, topic):
    if coll_id:
        return f'All tools from the {coll_id} collection.'
    elif topic:
        return f'All tools about the {topic} topic.'
    return 'All tools from a custom query'

def create_new_query(coll_id, topic, tools_list):
    if coll_id:
        coll_id = coll_id.split('"')[1]
    elif topic:
        topic = topic.split('"')[1]
    with Session() as session:
        new_query = db.queries(id=create_hash(), collection_id=coll_id, topic=topic, tools_list=tools_list)
        session.add(new_query)
        try:
            session.commit()
        except Exception as e:
            print(f'ROLLING BACK IN CREATING NEW QUERY {repr(e)}')
            session.rollback()

if __name__ == "__main__":
    app.run(debug=True)
