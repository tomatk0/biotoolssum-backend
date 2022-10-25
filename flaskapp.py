from flask import Flask, session, render_template, request, jsonify
import requests
import db
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from sqlalchemy.sql.expression import intersect
import math
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['CORS_HEADERS'] = 'Content-Type'

Session = sessionmaker(bind=db.engine)
session = Session()

def add_latest_version(versions):
    return versions[0] if versions else ''

def add_tool_types(tool_types, bio_id):
    already_used = []
    for name in tool_types:
        if name in already_used:
            continue
        already_used.append(name)
        new_tool_type = db.tool_types(bio_id=bio_id, name=name)
        session.add(new_tool_type)
    session.commit()

def add_institutes(credit, bio_id):
    for item in credit:
        if item['typeEntity'] == 'Institute':
            name = item['name']
            new_institute = db.institutes(bio_id=bio_id, name=name)
            session.add(new_institute)
    session.commit()

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
    session.commit()

def add_functions(functions, bio_id):
    already_used = []
    if not functions:
        return
    for item in functions[0]['operation']:
        term = item['term']
        uri = item['uri']
        if term in already_used:
            continue
        already_used.append(term)
        new_function = db.functions(bio_id=bio_id, term=term, uri=uri)
        session.add(new_function)
    session.commit()


def add_platforms(platforms, bio_id):
    for name in platforms:
        new_platform = db.platforms(bio_id=bio_id, name=name)
        session.add(new_platform)
    session.commit()

def add_years(citations, doi):
    years_dict = {}
    if not citations['citation']:
        return 
    for item in citations['citation']:
        year = str(item['pubYear'])
        years_dict[year] = years_dict.get(year, 0) + 1
    for key, val in years_dict.items():
        new_year = db.years(doi=doi, year=key, count=val)
        session.add(new_year)
    session.commit()

def add_input_output(functions, bio_id):
    if not functions:
        return
    input_terms = []
    for item in functions[0]['input']:
        term = item['data']['term']
        if term in input_terms:
            continue
        input_terms.append(term)
        new_input = db.inputs(bio_id=bio_id, term=term)
        session.add(new_input)
    output_terms = []
    for item in functions[0]['output']:
        term = item['data']['term']
        if term in output_terms:
            continue
        output_terms.append(term)
        new_output = db.outputs(bio_id=bio_id, term=term)
        session.add(new_output)
    session.commit()

def add_collection_ids(collection_ids, bio_id):
    already_used = []
    for coll_id in collection_ids:
        if coll_id in already_used:
            continue
        new_coll_id = db.collection_ids(bio_id=bio_id, coll_id=coll_id)
        session.add(new_coll_id)
    session.commit()

def add_publications_and_years(publications, bio_id):
    for publication in publications:
        pub_doi = publication['doi']
        if bool(session.query(db.publications).filter_by(doi=pub_doi).first()):
            continue
        pmid = publication['pmid']
        pmcid = publication['pmcid']
        if pub_doi:
            response = requests.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={pub_doi}&format=json').json()
        elif pmid:
            response = requests.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={pmid}&format=json').json()
        else:
            response = requests.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={pmcid}&format=json').json()
        result = response['resultList']['result']
        if result and not pub_doi:
            pub_doi = result[0]['doi']
        if result and not pmid:
            pmid = result[0]['id']
        response = requests.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/MED/{pmid}/citations/1/1000/json').json()
        add_years(response['citationList'], pub_doi)
        new_publication = db.publications(doi=pub_doi, bio_id=bio_id, pmid=pmid, pmcid=pmcid)
        session.add(new_publication)
    session.commit()

def add_tool(item, id):
    version = add_latest_version(item['version'])
    bio_link = f'https://bio.tools/{id}'
    homepage = item['homepage']
    add_tool_types(item['toolType'], id)
    add_institutes(item['credit'], id)
    description = item['description']
    add_topics(item['topic'], id)
    add_functions(item['function'], id)
    maturity = item['maturity']
    add_platforms(item['operatingSystem'], id)
    add_input_output(item['function'], id)
    license = item['license']
    add_collection_ids(item['collectionID'], id)
    add_publications_and_years(item['publication'], id)
    tool = db.tools(bio_id=id, version=version, bio_link=bio_link, homepage=homepage, description=description, maturity=maturity, license=license)
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
    tool.publications = get_publications_and_years_from_table(tool)
    tool.functions = get_data_from_table(tool, db.functions)
    tool.topics = get_data_from_table(tool, db.topics)
    tool.institutes = get_data_from_table(tool, db.institutes)
    tool.platforms = get_data_from_table(tool, db.platforms)
    tool.tool_types = get_data_from_table(tool, db.tool_types)
    tool.inputs = get_data_from_table(tool, db.inputs)
    tool.outputs = get_data_from_table(tool, db.outputs)
    tool.collection_ids = get_data_from_table(tool, db.collection_ids)

def get_tools_from_api(coll_id, topic, count_db):
    result = []
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
            session.add(tool)
            get_lists_for_tool(tool)
            result.append(tool.serialize())
    session.commit()
    return result

def get_tools_from_db(coll_id, topic):
    result = []
    coll_id_result = select(db.tools).where(db.tools.bio_id == db.collection_ids.bio_id, db.collection_ids.coll_id == coll_id)
    topic_result = select(db.tools).where(db.tools.bio_id == db.topics.bio_id, db.topics.term == topic)
    query = intersect(coll_id_result, topic_result)
    if coll_id and not topic:
        query = intersect(coll_id_result)
    elif not coll_id and topic:
        query = intersect(topic_result)
    for id in session.scalars(query):
        tool_select = select(db.tools).where(db.tools.bio_id == id)
        for tool in session.scalars(tool_select):
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

@app.route("/", methods=["POST", "GET"])
def get_parameters():
    existing_queries = get_existing_queries() 
    if request.method == "POST":
        coll_id_form = request.form.get("coll_id")
        topic_form = request.form.get("topic")
        if not coll_id_form and not topic_form:
            return render_template("get_parameters.html")
        only_names_form = 'off' if not request.form.get('only_names') else 'on'
        if bool(session.query(db.queries).filter_by(collection_id=coll_id_form, topic=topic_form, only_names=only_names_form).first()):
            return render_template("get_parameters.html", content=existing_queries)  
        new_query = db.queries(collection_id=coll_id_form, topic=topic_form, only_names=only_names_form)
        session.add(new_query)
        session.commit()
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
        return get_tools(query.collection_id, query.topic, query.only_names)

def get_tools(coll_id, topic, only_names):
    result_db = get_tools_from_db(coll_id, topic)
    count_db = len(result_db)
    print(f'TOOLS FROM DB:{count_db}')
    coll_id = f'&collectionID=\"{coll_id}\"' if coll_id else ''
    topic = f'&topic=\"{topic}\"' if topic else ''
    result_api = get_tools_from_api(coll_id, topic, count_db)
    print(f'TOOLS FROM API:{len(result_api)}')
    result_db.extend(result_api)
    result = show_only_names(result_db, only_names)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
