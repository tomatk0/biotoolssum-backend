import requests
import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import common.db as db

Session = sessionmaker(bind=db.engine, autoflush=False)

def update_version(versions):
    if not versions:
        return ""
    if versions[0][0] == "v":
        return versions[0]
    return "v" + versions[0]

def update_availability(id):
    response = requests.get(f"https://openebench.bsc.es/monitor/rest/aggregate?id={id.lower()}")
    if not response.ok:
        return None
    response = response.json()
    if not response or "entities" not in response[0]:
        return None
    entities = response[0]["entities"]
    link = ""
    for entity in entities:
        if entity["type"] == "web":
            link = entity["tools"][-1]["@id"]
            break
        elif entity["type"]:
            link = entity["tools"][-1]["@id"]
    if not link:
        return None
    split_link = link.split("/")
    response = requests.get(
        f"https://openebench.bsc.es/monitor/rest/homepage/{split_link[-3]}/{split_link[-2]}/{split_link[-1]}?limit=8"
    )
    if not response.ok:
        return None
    response = response.json()
    codes_200 = 0
    for item in response:
        if item["code"] == 200:
            codes_200 += 1
    return str(round(100 * (codes_200 / 8)))

def update_github_info(link):
    github_url = ""
    for item in link:
        if "Repository" in item["type"] and "github" in item["url"]:
            github_url = item["url"]
            break
    if not github_url:
        return None, None, None, None, None, None
    github_url = github_url[:-1] if github_url[-1] == "/" else github_url
    owner_and_repo = github_url.split("/")[-2:]
    if owner_and_repo[0] == 'github.com':
        return None, None, None, None, None, None
    response = requests.get(
        f"https://api.github.com/repos/{owner_and_repo[0]}/{owner_and_repo[1]}",
        auth=(
            "493043@mail.muni.cz",
            "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",
        ),
    )
    if not response.ok:
        return None, None, None, None, None, None
    response = response.json()
    if "message" in response:
        return github_url, None, None, None, None, None
    created_at = (
        "" if "created_at" not in response else response["created_at"].split("T")[0]
    )
    updated_at = (
        "" if "updated_at" not in response else response["updated_at"].split("T")[0]
    )
    forks = 0 if "forks" not in response else response["forks"]
    stars = 0 if "stargazers_count" not in response else response["stargazers_count"]
    response = requests.get(
        f"https://api.github.com/repos/{owner_and_repo[0]}/{owner_and_repo[1]}/contributors",
        auth=(
            "493043@mail.muni.cz",
            "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",
        ),
    )
    if not response.ok:
        return (
            None, None, None, None, None, None
        )
    response = response.json()
    contributions = 0
    if isinstance(response, list):
        for user in response:
            contributions += user['contributions']
    return github_url, created_at, updated_at, forks, contributions, stars

def get_years_for_graphs(doi):
    response = requests.get(f"https://badge.dimensions.ai/details/doi/{doi}/cited_works.json?domain=https://bio.tools")
    if not response.ok:
        return
    response = response.json()
    years_list = [] if 'years' not in response else response['years']
    if not years_list:
        return
    result = {}
    for year in years_list:
        count, id = year['count'], year['id']
        result[id] = count
    return result

def create_options_for_graphs(tool_name, years_for_graphs):
    if not years_for_graphs:
        return
    all_years = []
    for publication in years_for_graphs.values():
        if not publication:
            continue
        for key in publication.keys():
            all_years.append(key)
    if not all_years:
        return
    min_year = min(all_years)
    max_year = max(all_years)
    years_list = []
    current_year = min_year
    while current_year <= max_year:
        years_list.append(current_year)
        current_year += 1
    series = []
    for title, years in years_for_graphs.items():
        series_item = {}
        series_item['name'] = title
        series_item['data'] = []
        if not years:
            for year in years_list:
                series_item['data'].append(0)
            series.append(series_item)
            continue
        for year in years_list:
            series_item['data'].append(years.get(year, 0))
        series.append(series_item)
    options = {
        'title': {
            'text': f'Citations for {tool_name}'
        },
        'exporting': {
            'filename': f'chart_{tool_name}',
            'buttons': {
                'contextButton': {
                    'text': 'Generate',
                    'symbolY': 15
                }
            },
            'chartOptions': {
                'plotOptions': {
                    'series': {
                        'dataLabels': {
                            'enabled': True
                        }
                    }
                }
            }
        },
        'chart': {
            'type': 'column'
        },
        'tooltip': {
        
        },
        'xAxis': {
            'categories': years_list
        },
        'yAxis': {
            'title': {
                'text': 'Citations'
            },
            'allowDecimals': False
        },
        'plotOptions': {
            'series': {
                'pointWidth': 20
            }
        },
        'series': series
    }
    json_options = json.dumps(options)
    return json_options.encode()

def create_display_string(coll_id, topic):
    if coll_id:
        return f'All tools from the {coll_id} collection'
    elif topic:
        return f'All tools about the {topic} topic'
    return 'All tools from a custom query'

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

def get_data_from_tables(tool, tables):
    with Session() as session:
        result = {}
        for table in tables:
            query = select(table).where(table.bio_id == tool.bio_id)
            result[table.__tablename__] = [item.serialize() for item in session.scalars(query)]
    return result

def get_lists_for_tool(tool):
    tables = [db.matrix_queries, db.functions, db.topics, db.institutes, db.platforms, db.tool_types, db.inputs, db.outputs, db.collection_ids, db.documentations, db.elixir_platforms, db.elixir_nodes, db.elixir_communities]
    data = get_data_from_tables(tool, tables)
    tool.matrix_queries = data['matrix_queries']
    tool.publications = get_publications_and_years_from_table(tool)
    tool.functions = data['functions']
    tool.topics = data['topics']
    tool.institutes = data['institutes']
    tool.platforms = data['platforms']
    tool.tool_types = data['tool_types']
    tool.inputs = data['inputs']
    tool.outputs = data['outputs']
    tool.collection_ids = data['collection_ids']
    tool.documentations = data['documentations']
    tool.elixir_platforms = data['elixir_platforms']
    tool.elixir_nodes = data['elixir_nodes']
    tool.elixir_communities = data['elixir_communities']

def separate_tools_by_matrix_queries(serialized_tools):
    separated_tools = {"dna sequence": [], "dna secondary structure": [], "dna structure": [], "genomics": [], "rna sequence": [], "rna secondary structure": [], "rna structure": [], "rna omics": [], "protein sequence": [], "protein secondary structure": [], "protein structure": [], "protein omics": [], "small molecule primary sequence": [], "small molecule secondary structure": [], "small molecule structure": [], "small molecule omics": []}
    for tool in serialized_tools:
        for matrix_query in tool['matrix_queries']:
            separated_tools[matrix_query['matrix_query']].append(tool)
    result = []
    result_sizes = []
    for value in separated_tools.values():
        result.append(value)
        result_sizes.append(len(value))
    return result, result_sizes


def get_tools_from_db(coll_id, topic, tools_list):
    result = []
    with Session() as session:
        if tools_list:
            for tool in tools_list.split(','):
                t = session.scalars(select(db.tools).where(db.tools.bio_id == tool)).first()
                get_lists_for_tool(t)
                result.append(t.serialize())
            matrix_tools, matrix_tools_sizes = separate_tools_by_matrix_queries(result)
            return result, matrix_tools, matrix_tools_sizes
        
        if coll_id:
            query = select(db.tools).distinct().where(db.tools.bio_id == db.collection_ids.bio_id, db.collection_ids.coll_id.ilike(f'{coll_id}'))
        elif topic:
            query = select(db.tools).distinct().where(db.tools.bio_id == db.topics.bio_id, db.topics.term.ilike(f'%{topic}%'))
        for tool in session.scalars(query):
            get_lists_for_tool(tool)
            result.append(tool.serialize())
        matrix_tools, matrix_tools_sizes = separate_tools_by_matrix_queries(result)
        return result, matrix_tools, matrix_tools_sizes
    