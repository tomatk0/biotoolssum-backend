from flask import Flask, session
import requests
import db
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import math

app = Flask(__name__)

Session = sessionmaker(bind=db.engine)
session = Session()

def get_latest_version(versions):
    return versions[0] if versions else ''

def get_tool_types(tool_types, bio_id):
    for name in tool_types:
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
    terms = []
    for item in topics:
        term = item['term']
        uri = item['uri']
        if term in terms:
            continue
        terms.append(term)
        new_topic = db.topics(bio_id, term, uri)
        session.add(new_topic)
    session.commit()

def get_functions(functions, bio_id):
    if not functions:
        return
    for item in functions[0]['operation']:
        term = item['term']
        uri = item['uri']
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
    for item in functions[0]['output']:
        term = item['data']['term']
        new_output = db.outputs(bio_id, term)
        session.add(new_output)
    session.commit()

def get_collection_ids(collection_ids, bio_id):
    for coll_id in collection_ids:
        new_coll_id = db.collection_ids(bio_id, coll_id)
        session.add(new_coll_id)
    session.commit()

@app.route("/get_tools_from_api")
def get_tools_from_api():
    filtered_list = []
    response = requests.get('https://bio.tools/api/tool/?&collectionID="elixir-cz"&format=json').json()
    count = math.ceil(response['count'] / 10) + 1
    for i in range(1, count):
        response = requests.get(f'https://bio.tools/api/tool/?page={i}&collectionID="elixir-cz"&format=json').json()
        for item in response['list']:
            bio_id = item['biotoolsID']
            version = get_latest_version(item['version'])
            bio_link = f'https://bio.tools/{bio_id}'
            homepage = item['homepage']
            get_tool_types(item['toolType'], bio_id)
            get_institutes(item['credit'], bio_id)
            description = item['description']
            total_citations = 0
            get_topics(item['topic'], bio_id)
            get_functions(item['function'], bio_id)
            maturity = item['maturity']
            cost = item['cost']
            get_platforms(item['operatingSystem'], bio_id)
            get_input_output(item['function'], bio_id)
            license = item['license']
            get_collection_ids(item['collectionID'], bio_id)
            for publication in item['publication']:
                doi = publication['doi']
                pmid = publication['pmid']
                pmcid = publication['pmcid']
                if doi:
                    response = requests.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={doi}&format=json').json()
                elif pmid:
                    response = requests.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={pmid}&format=json').json()
                else:
                    response = requests.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={pmcid}&format=json').json()
                result = response['resultList']['result']
                if result:
                    pmid = result[0]['id']
                    doi = result[0]['doi']
                response = requests.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/MED/{pmid}/citations/1/1000/json').json()
                total_citations += response['hitCount']
                new_publication = db.publications(doi, bio_id, pmid, pmcid)
                session.add(new_publication)
            tool = db.tools(bio_id, version, bio_link, homepage, description, total_citations, maturity, cost, license)
            session.add(tool)
    session.commit()
    return filtered_list

# Shows a tool and then it's publications in a list
@app.route("/")
def show_tools():
    tools = select(db.tools)
    result = []
    for tool in session.scalars(tools):
        result.append(tool.serialize())
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

if __name__ == "__main__":
    app.run(debug=True)