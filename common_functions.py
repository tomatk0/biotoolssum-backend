import requests

def update_version(versions):
    if not versions:
        return ''
    if versions[0][0] == 'v':
        return versions[0]
    return 'v' + versions[0]

def update_availability(id):
    response = requests.get(f'https://openebench.bsc.es/monitor/rest/aggregate?id={id}').json()
    if not response or 'entities' not in response[0]:
        return 0
    entities = response[0]['entities']
    link = ''
    for entity in entities:
        if entity['type'] == 'web':
            link = entity['tools'][-1]['@id']
            break
        elif entity['type']:
            link = entity['tools'][-1]['@id']
    if not link:
        return 0
    split_link = link.split('/')
    response = requests.get(f'https://openebench.bsc.es/monitor/rest/homepage/{split_link[-3]}/{split_link[-2]}/{split_link[-1]}?limit=8').json()
    codes_200 = 0
    for item in response:
        if item['code'] == 200:
            codes_200 += 1
    return round(100 * (codes_200/8))

def update_github_info(link):
    github_url = ''
    for item in link:
        if 'Repository' in item['type'] and 'github' in item['url']:
            github_url = item['url']
    if not github_url:
        return '', '', '', 0, 0
    github_url = github_url[:-1] if github_url[-1] == '/' else github_url
    owner_and_repo = github_url.split('/')[-2:]
    response = requests.get(f'https://api.github.com/repos/{owner_and_repo[0]}/{owner_and_repo[1]}', auth=('493043@mail.muni.cz', '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')).json()
    if 'message' in response:
        return github_url, '', '', 0, 0
    created_at = '' if 'created_at' not in response else response['created_at'].split('T')[0]
    updated_at = '' if 'updated_at' not in response else response['updated_at'].split('T')[0]
    forks = 0 if 'forks' not in response else response['forks']
    response = requests.get(f'https://api.github.com/repos/{owner_and_repo[0]}/{owner_and_repo[1]}/contributors', auth=('493043@mail.muni.cz', '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')).json()
    contributions = 0 if not response or 'contributions' not in response[0] else response[0]['contributions']
    return github_url, created_at, updated_at, forks, contributions

def get_doi_pmid_source(pub_doi, pmid, pmcid):
    if pub_doi:
        response = requests.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={pub_doi}&pageSize=1000&format=json').json()
    elif pmid:
        response = requests.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={pmid}&pageSize=1000&format=json').json()
    result = response['resultList']['result'] if response['resultList'] else []
    source = ''
    for item in result:
        source = item['source']
        if 'doi' in item and item['doi'] == pub_doi:
            pmid = item['id'] if 'id' in item else pmid
            break
        if 'id' in item and (item['id'] == pmid or item['id'] == pmcid):
            pub_doi = item['doi'] if 'doi' in item else pub_doi
            break
    return pub_doi, pmid, source

def add_years(doi, pmid, session, db):
    response = requests.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/MED/{pmid}/citations/1/1000/json').json()
    citation_count = response['hitCount']
    if citation_count < 1:
        return 0, '2022', '2022'
    number_of_pages = (response['hitCount'] // 1000) + 1
    years_dict = {}
    for i in range(1, number_of_pages + 1):
        response = requests.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/MED/{pmid}/citations/{i}/1000/json').json()
        for item in response['citationList']['citation']:
            year = str(item['pubYear'])
            years_dict[year] = years_dict.get(year, 0) + 1
    keys_list = list(years_dict.keys())
    min_year = '2022' if not keys_list else min(keys_list)
    max_year = '2022' if not keys_list else max(keys_list)
    for key, val in years_dict.items():
        if bool(session.query(db.years).filter_by(doi=doi, year=key, count=val).first()):
            return citation_count, min_year, max_year
        new_year = db.years(doi=doi, year=key, count=val)
        session.add(new_year)
    try:
        session.commit()
    except:
        session.rollback()
    return citation_count, min_year, max_year