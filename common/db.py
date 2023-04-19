from sqlalchemy import Column, String, Integer, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy.types import LargeBinary
import json

engine = create_engine('mysql+pymysql://biotoolsDB:password@localhost/bio20', poolclass=NullPool)
base = declarative_base()


class tools(base):
    __tablename__ = "tools"

    bio_id = Column(String(255), primary_key=True)
    name = Column(String(255))
    version = Column(String(255))
    bio_link = Column(String(255))
    homepage = Column(String(255))
    description = Column(String(5000))
    maturity = Column(String(255))
    license = Column(String(255))
    citation_count = Column(Integer)
    impact_factor = Column(Float)
    journals = Column(String(255))
    availability = Column(String(255))
    github_url = Column(String(255))
    github_created_at = Column(String(255))
    github_updated_at = Column(String(255))
    github_forks = Column(Integer)
    github_contributions = Column(Integer)
    github_stars = Column(Integer)
    last_updated = Column(String(255))
    options_for_graph = Column(LargeBinary)
    matrix_queries = []
    publications = []
    functions = []
    topics = []
    institutes = []
    platforms = []
    tool_types = []
    inputs = []
    outputs = []
    collection_ids = []
    documentations = []
    elixir_platforms = []
    elixir_nodes = []
    elixir_communities = []

    def serialize(self):
        return {
            "bio_id": self.bio_id,
            "name": self.name,
            "version": self.version,
            "bio_link": self.bio_link,
            "homepage": self.homepage,
            "description": self.description,
            "maturity": self.maturity,
            "license": self.license,
            "citation_count": self.citation_count,
            "impact_factor": self.impact_factor,
            "journals": self.journals,
            "availability": self.availability,
            "github_url": self.github_url,
            "github_created_at": self.github_created_at,
            "github_updated_at": self.github_updated_at,
            "github_forks": self.github_forks,
            "github_contributions": self.github_contributions,
            "github_stars": self.github_stars,
            "matrix_queries": self.matrix_queries,
            "publications": self.publications,
            "functions": self.functions,
            "topics": self.topics,
            "institutes": self.institutes,
            "platforms": self.platforms,
            "tool_types": self.tool_types,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "collection_ids": self.collection_ids,
            "documentations": self.documentations,
            "elixir_platforms": self.elixir_platforms,
            "elixir_nodes": self.elixir_nodes,
            "elixir_communities": self.elixir_communities,
            "last_updated": self.last_updated,
            "options_for_graph": None if not self.options_for_graph else json.loads(self.options_for_graph.decode('utf-8'))
        }


class publications(base):
    __tablename__ = "publications"

    doi = Column(String(255), primary_key=True)
    bio_id = Column(String(255), primary_key=True)
    pmid = Column(String(255))
    title = Column(String(255))
    authors = Column(String(5000))
    journal = Column(String(255))
    impact = Column(Float)
    publication_date = Column(String(255))
    citations_count = Column(Integer)
    citations_source = Column(String(255))
    citations_list = []

    def serialize(self):
        return {
            "doi": self.doi,
            "pmid": self.pmid,
            "title": self.title,
            "authors": self.authors,
            "journal": self.journal,
            "impact": self.impact,
            "publication_date": self.publication_date,
            "citations_count": self.citations_count,
            "citations_source": self.citations_source,
            "citations_list": self.citations_list,
        }


class years(base):
    __tablename__ = "years"

    doi = Column(String(255), primary_key=True)
    year = Column(String(255), primary_key=True)
    count = Column(String(255))

    def serialize(self):
        return {"year": self.year, "count": self.count}


class functions(base):
    __tablename__ = "functions"

    bio_id = Column(String(255), primary_key=True)
    term = Column(String(255), primary_key=True)
    uri = Column(String(255))

    def serialize(self):
        return {"term": self.term, "uri": self.uri}


class topics(base):
    __tablename__ = "topics"

    bio_id = Column(String(255), primary_key=True)
    term = Column(String(255), primary_key=True)
    uri = Column(String(255))

    def serialize(self):
        return {"term": self.term, "uri": self.uri}


class institutes(base):
    __tablename__ = "institutes"

    bio_id = Column(String(255), primary_key=True)
    name = Column(String(255), primary_key=True)

    def serialize(self):
        return {"name": self.name}


class platforms(base):
    __tablename__ = "platforms"

    bio_id = Column(String(255), primary_key=True)
    name = Column(String(255), primary_key=True)

    def serialize(self):
        return {"name": self.name}


class tool_types(base):
    __tablename__ = "tool_types"

    bio_id = Column(String(255), primary_key=True)
    name = Column(String(255), primary_key=True)

    def serialize(self):
        return {"name": self.name}


class inputs(base):
    __tablename__ = "inputs"

    bio_id = Column(String(255), primary_key=True)
    term = Column(String(255), primary_key=True)

    def serialize(self):
        return {"term": self.term}


class outputs(base):
    __tablename__ = "outputs"

    bio_id = Column(String(255), primary_key=True)
    term = Column(String(255), primary_key=True)

    def serialize(self):
        return {"term": self.term}


class collection_ids(base):
    __tablename__ = "collection_ids"

    bio_id = Column(String(255), primary_key=True)
    coll_id = Column(String(255), primary_key=True)

    def serialize(self):
        return {"coll_id": self.coll_id}

class documentations(base):
    __tablename__ = "documentations"

    bio_id = Column(String(255), primary_key=True)
    url = Column(String(255), primary_key=True)
    type = Column(String(255))

    def serialize(self):
        return {
            "url": self.url,
            "type": self.type
        }

class elixir_platforms(base):
    __tablename__ = "elixir_platforms"

    bio_id = Column(String(255), primary_key=True)
    name = Column(String(255), primary_key=True)

    def serialize(self):
        return {"name": self.name}


class elixir_nodes(base):
    __tablename__ = "elixir_nodes"

    bio_id = Column(String(255), primary_key=True)
    name = Column(String(255), primary_key=True)

    def serialize(self):
        return {"name": self.name}


class elixir_communities(base):
    __tablename__ = "elixir_communities"

    bio_id = Column(String(255), primary_key=True)
    name = Column(String(255), primary_key=True)

    def serialize(self):
        return {"name": self.name}


class queries(base):
    __tablename__ = "queries"

    id = Column(String(255), primary_key=True)
    collection_id = Column(String(255))
    topic = Column(String(255))
    tools_list = Column(String(255))


class matrix_queries(base):
    __tablename__ = "matrix_queries"

    bio_id = Column(String(255), primary_key=True)
    matrix_query = Column(String(255), primary_key=True)

    def serialize(self):
        return {"matrix_query": self.matrix_query}
    
class finished_jsons(base):
    __tablename__ = "finished_jsons"

    id = Column(String(255), primary_key=True)
    data = Column(LargeBinary(100000000))


base.metadata.create_all(engine)
