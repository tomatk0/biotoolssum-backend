from flask import Flask, session, render_template, request
import requests
import db
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from sqlalchemy.sql.expression import intersect
import math

app = Flask(__name__)

Session = sessionmaker(bind=db.engine)
session = Session()

def get_latest_version(versions):
    return versions[0] if versions else ''

def get_tool_types(tool_types, bio_id):
    already_used = []
    for name in tool_types:
        if name in already_used:
            continue
        already_used.append(name)
        new_tool_type = db.tool_types(bio_id, name)
        session.add(new_tool_type)
    session.commit()

def get_institutes(credit, bio_id):
    for item in credit:
        if item['typeEntity'] == 'Institute':
            name = item['name']
            new_institute = db.institutes(bio_id, name)
            session.add(new_institute)
    session.commit()

def get_topics(topics, bio_id):
    already_used = []
    for item in topics:
        term = item['term']
        uri = item['uri']
        if term in already_used:
            continue
        already_used.append(term)
        new_topic = db.topics(bio_id, term, uri)
        session.add(new_topic)
    session.commit()

def get_functions(functions, bio_id):
    already_used = []
    if not functions:
        return
    for item in functions[0]['operation']:
        term = item['term']
        uri = item['uri']
        if term in already_used:
            continue
        already_used.append(term)
        new_function = db.functions(bio_id, term, uri)
        session.add(new_function)
    session.commit()


def get_platforms(platforms, bio_id):
    for name in platforms:
        new_platform = db.platforms(bio_id, name)
        session.add(new_platform)
    session.commit()

def get_years(citations, doi):
    years = {}
    if not citations['citation']:
        return 
    for item in citations['citation']:
        year = str(item['pubYear'])
        years[year] = years.get(year, 0) + 1
    for key, val in years.items():
        new_year = db.years(doi, key, str(val))
        session.add(new_year)
    session.commit()

def get_input_output(functions, bio_id):
    if not functions:
        return
    input_terms = []
    for item in functions[0]['input']:
        term = item['data']['term']
        if term in input_terms:
            continue
        input_terms.append(term)
        new_input = db.inputs(bio_id, term)
        session.add(new_input)
    output_terms = []
    for item in functions[0]['output']:
        term = item['data']['term']
        if term in output_terms:
            continue
        output_terms.append(term)
        new_output = db.outputs(bio_id, term)
        session.add(new_output)
    session.commit()

def get_collection_ids(collection_ids, bio_id):
    already_used = []
    for coll_id in collection_ids:
        if coll_id in already_used:
            continue
        new_coll_id = db.collection_ids(bio_id, coll_id)
        session.add(new_coll_id)
    session.commit()

def get_data_from_other_tables(tool):
    result = []
    publications = select(db.publications).where(db.publications.bio_id == tool.bio_id)
    for publication in session.scalars(publications):
        result.append(publication.serialize())
        years = select(db.years).where(db.years.doi == publication.doi)
        for year in session.scalars(years):
            result.append(year.serialize())
    functions = select(db.functions).where(db.functions.bio_id == tool.bio_id)
    for function in session.scalars(functions):
        result.append(function.serialize())
    institutes = select(db.institutes).where(db.institutes.bio_id == tool.bio_id)
    for institute in session.scalars(institutes):
        result.append(institute.serialize())
    topics = select(db.topics).where(db.topics.bio_id == tool.bio_id)
    for topic in session.scalars(topics):
        result.append(topic.serialize())
    platforms = select(db.platforms).where(db.platforms.bio_id == tool.bio_id)
    for platform in session.scalars(platforms):
        result.append(platform.serialize())
    tool_types = select(db.tool_types).where(db.tool_types.bio_id == tool.bio_id)
    for tool_type in session.scalars(tool_types):
        result.append(tool_type.serialize())
    inputs = select(db.inputs).where(db.inputs.bio_id == tool.bio_id)
    for input in session.scalars(inputs):
        result.append(input.serialize())
    outputs = select(db.outputs).where(db.outputs.bio_id == tool.bio_id)
    for output in session.scalars(outputs):
        result.append(output.serialize())
    collection_ids = select(db.collection_ids).where(db.collection_ids.bio_id == tool.bio_id)
    for coll_id in session.scalars(collection_ids):
        result.append(coll_id.serialize())
    return result

def get_tools_from_api(coll_id, topic, count_db):
    result = []
    response = requests.get(f'https://bio.tools/api/tool/?{coll_id}{topic}&format=json').json()
    count_api = response['count'] - count_db
    if count_api == 0:
        return result, 0
    count = math.ceil(response['count'] / 10) + 1
    for i in range(1, count):
        response = requests.get(f'https://bio.tools/api/tool/?page={i}{coll_id}{topic}&format=json').json()
        for item in response['list']:
            id = item['biotoolsID']
            if bool(session.query(db.tools).filter_by(bio_id=id).first()):
                continue
            version = get_latest_version(item['version'])
            bio_link = f'https://bio.tools/{id}'
            homepage = item['homepage']
            get_tool_types(item['toolType'], id)
            get_institutes(item['credit'], id)
            description = item['description']
            total_citations = 0
            get_topics(item['topic'], id)
            get_functions(item['function'], id)
            maturity = item['maturity']
            cost = item['cost']
            get_platforms(item['operatingSystem'], id)
            get_input_output(item['function'], id)
            license = item['license']
            get_collection_ids(item['collectionID'], id)
            for publication in item['publication']:
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
                total_citations += response['hitCount']
                new_publication = db.publications(pub_doi, id, pmid, pmcid)
                session.add(new_publication)
            tool = db.tools(id, version, bio_link, homepage, description, total_citations, maturity, cost, license)
            session.add(tool)
            result.append(tool.serialize())
            data = get_data_from_other_tables(tool)
            result.extend(data)
    session.commit()
    return result, count_api

def get_tools_from_db(coll_id, topic):
    result = []
    count = 0
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
            result.append(tool.serialize())
            data = get_data_from_other_tables(tool)
            result.extend(data)
            count += 1
    return result, count

@app.route("/", methods=["POST", "GET"])
def get_parameters():
    if request.method == "POST":
        coll_id_form = request.form["coll_id"]
        topic_form = request.form["topic"]
        return get_tools(coll_id_form, topic_form)
    return render_template("get_parameters.html")

def get_tools(coll_id, topic):
    result_db, count_db = get_tools_from_db(coll_id, topic)
    print(f'TOOLS FROM DB:{count_db}')
    coll_id = f'&collectionID=\"{coll_id}\"' if coll_id else ''
    topic = f'&topic=\"{topic}\"' if topic else ''
    result_api, count_api = get_tools_from_api(coll_id, topic, count_db)
    print(f'TOOLS FROM API:{count_api}')
    result_db.extend(result_api)
    return result_db

if __name__ == "__main__":
    app.run(debug=True)
