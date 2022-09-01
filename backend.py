from flask import Flask, session
import requests
import db
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

app = Flask(__name__)

Session = sessionmaker(bind=db.engine)
session = Session()

def get_latest_version(versions):
    return versions[0] if versions else ''

def get_tool_types(tool_types):
    result = ''
    for item in tool_types:
        result += f'{item}|'
    return result[:-1]

def get_institutes(credit):
    result = ''
    for item in credit:
        if item['typeEntity'] == 'Institute':
            name = item['name']
            result += f'{name}|'
    return result[:-1]

def get_topics(topics):
    result = ''
    for item in topics:
        term = item['term']
        uri = item['uri']
        result += f'{term}|{uri}|'
    return result[:-1]

def get_functions(functions):
    result = ''
    if not functions:
        return result
    for item in functions[0]['operation']:
        term = item['term']
        uri = item['uri']
        result += f'{term}|{uri}|'
    return result[:-1]

def get_platforms(platforms):
    result = ''
    for item in platforms:
        result += f'{item}|'
    return result[:-1]

def get_years(citations):
    years = {}
    result = ''
    if not citations['citation']:
        return ''
    for item in citations['citation']:
        year = item['pubYear']
        years[year] = years.get(year, 0) + 1
    for key, val in years.items():
        result += f'{key}:{val}|'
    return result[:-1]

def get_input_output(functions):
    input = ''
    output = ''
    if not functions:
        return input, output
    for item in functions[0]['input']:
        term = item['data']['term']
        input += f'{term}|'
    for item in functions[0]['output']:
        term = item['data']['term']
        output += f'{term}|'
    return input[:-1], output[:-1]

@app.route("/get_tools")
def get_data():
    filtered_list = []
    publication_id = 1
    for i in range(1, 9):
        response = requests.get(f'https://bio.tools/api/tool/?page={i}&collectionID="elixir-cz"&format=json').json()
        for item in response['list']:
            bio_id = item['biotoolsID']
            version = get_latest_version(item['version'])
            bio_link = f'https://bio.tools/{bio_id}'
            homepage = item['homepage']
            tool_type = get_tool_types(item['toolType'])
            institute = get_institutes(item['credit'])
            description = item['description']
            total_citations = 0
            topic = get_topics(item['topic'])
            function = get_functions(item['function'])
            maturity = item['maturity']
            platforms = get_platforms(item['operatingSystem'])
            input, output = get_input_output(item['function'])
            license = item['license']
            for publication in item['publication']:
                id = publication_id
                publication_id += 1
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
                response = requests.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/MED/{pmid}/citations/1/1000/json').json()
                total_citations += response['hitCount']
                years = get_years(response['citationList'])
                new_publication = db.publications(id, bio_id, doi, pmid, pmcid, years)
                session.add(new_publication)
            tool = db.tools(bio_id, version, bio_link, homepage, tool_type, institute, description, total_citations, topic, function, maturity, platforms, input, output, license)
            session.add(tool)
    session.commit()
    return filtered_list

@app.route("/")
def show_tools():
    stmt = select(db.tools)
    result = []
    for tool in session.scalars(stmt):
        result.append(tool.serialize())
    return result

# @app.route("/show_publications")
# def show_publications():
#     stmt2 = select(db.publications)
#     result = []
#     for publication in session.scalars(stmt2):
#         result.append(publication.serialize())
#     return result

if __name__ == "__main__":
    app.run(debug=True)