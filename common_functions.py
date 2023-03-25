import requests

def update_version(versions):
    if not versions:
        return ""
    if versions[0][0] == "v":
        return versions[0]
    return "v" + versions[0]

def update_availability(id):
    response = requests.get(f"https://openebench.bsc.es/monitor/rest/aggregate?id={id.lower()}")
    if not response.ok:
        return "Not available"
    response = response.json()
    if not response or "entities" not in response[0]:
        return "Not available"
    entities = response[0]["entities"]
    link = ""
    for entity in entities:
        if entity["type"] == "web":
            link = entity["tools"][-1]["@id"]
            break
        elif entity["type"]:
            link = entity["tools"][-1]["@id"]
    if not link:
        return "0"
    split_link = link.split("/")
    response = requests.get(
        f"https://openebench.bsc.es/monitor/rest/homepage/{split_link[-3]}/{split_link[-2]}/{split_link[-1]}?limit=8"
    )
    if not response.ok:
        return "Not available"
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
        return "", "", "", "0", "0"
    github_url = github_url[:-1] if github_url[-1] == "/" else github_url
    owner_and_repo = github_url.split("/")[-2:]
    if owner_and_repo[0] == 'github.com':
        return "", "", "", "0", "0"
    response = requests.get(
        f"https://api.github.com/repos/{owner_and_repo[0]}/{owner_and_repo[1]}",
        auth=(
            "493043@mail.muni.cz",
            "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",
        ),
    )
    if not response.ok:
        return (
            "Not available",
            "Not available",
            "Not available",
            "Not available",
            "Not available",
        )
    response = response.json()
    if "message" in response:
        return github_url, "", "", "0", "0"
    created_at = (
        "" if "created_at" not in response else response["created_at"].split("T")[0]
    )
    updated_at = (
        "" if "updated_at" not in response else response["updated_at"].split("T")[0]
    )
    forks = "0" if "forks" not in response else str(response["forks"])
    response = requests.get(
        f"https://api.github.com/repos/{owner_and_repo[0]}/{owner_and_repo[1]}/contributors",
        auth=(
            "493043@mail.muni.cz",
            "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",
        ),
    )
    if not response.ok:
        return (
            "Not available",
            "Not available",
            "Not available",
            "Not available",
            "Not available",
        )
    response = response.json()
    contributions = 0
    if isinstance(response, list):
        for user in response:
            contributions += user['contributions']
    return github_url, created_at, updated_at, forks, str(contributions)

def get_citation_count_and_details(item):
    author_string = (
        "" if "authorString" not in item else item["authorString"] + ", "
    )
    title = "" if "title" not in item else item["title"] + ", "
    journal_title = (
        "" if "journalTitle" not in item else item["journalTitle"] + ", "
    )
    pub_year = "" if "pubYear" not in item else item["pubYear"] + ", "
    page_info = "" if "pageInfo" not in item else item["pageInfo"]
    details = author_string + title + journal_title + pub_year + page_info
    citation_count = 0 if "citedByCount" not in item else item["citedByCount"]
    return citation_count, details


def get_doi_pmid_source_details_citation_count(pub_doi, pmid, pmcid):
    if pub_doi:
        response = requests.get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={pub_doi}&pageSize=1000&format=json")
    elif pmid:
        response = requests.get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={pmid}&pageSize=1000&format=json")
    elif pmcid:
        response = requests.get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={pmcid}&pageSize=1000&format=json")
    if not response.ok:
        return "Not available", "Not available", "Not available", "Not available", 0
    response = response.json()
    result = response["resultList"]["result"] if response["resultList"] else []
    source = ""
    details = ""
    citation_count = 0
    for item in result:
        source = item["source"]
        if "doi" in item and item["doi"] == pub_doi:
            pmid = item["id"] if "id" in item else pmid
            citation_count, details = get_citation_count_and_details(item)
            break
        if "id" in item and (item["id"] == pmid or item["id"] == pmcid):
            pub_doi = item["doi"] if "doi" in item else pub_doi
            citation_count, details = get_citation_count_and_details(item)
            break
    return pub_doi, pmid, source, details, citation_count