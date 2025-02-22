import sys
from pydantic import BaseModel
import uvicorn

from aiocache import cached, Cache
from aiocache.serializers import PickleSerializer
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from typing import Optional, Union

from SearchEngineAPIClient import SearchEngineAPIClient

global search_engine_client

# ===============================================================
# ========================= API SERVER ==========================
# ===============================================================

app = FastAPI()
# seach_engine = load_search_engine()
# metadata = load_metadata()

#origins = [
#    "http://localhost:3000",
#    "http://localhost:3001",
#    "http://localhost:3002",
#    "http://localhost:3003",
#    "http://localhost:3004",
#    "http://localhost:3005",
#    "https://search.storyhunter.live"
#    "localhost"
#]
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/test")
def test(request: Request):
    if request.method == 'GET':
        return JSONResponse(content="Hello world from frontend api", status_code=200)


class QueryParameters(BaseModel):
    q: str
    p: int
    l: int
    tags: Optional[str] = None

    # valid filter params:
    singleChapter: Optional[Union[bool, str]] = None
    completionStatus: Optional[str] = None
    # language: Optional[str] = None
    wordCountFrom: Optional[Union[str, int]] = None
    wordCountTo: Optional[Union[str, int]] = None
    hitCountFrom: Optional[Union[str, int]] = None
    hitCountTo: Optional[Union[str, int]] = None
    kudosCountFrom: Optional[Union[str, int]] = None
    kudosCountTo: Optional[Union[str, int]] = None
    commentCountFrom: Optional[Union[str, int]] = None
    commentCountTo: Optional[Union[str, int]] = None
    bookmarkCountFrom: Optional[Union[str, int]] = None
    bookmarkCountTo: Optional[Union[str, int]] = None
    lastUpdatedFrom: Optional[str] = None
    lastUpdatedTo: Optional[str] = None


@app.get("/query")
async def read_query(request: Request):
    # print(dict(request.query_params))
    query_parameters = QueryParameters(**dict(request.query_params))

    if query_parameters.tags:
        tags = [t for t in query_parameters.tags.split(',') if t]
    else:
        tags = []

    # print(query_parameters.dict().items())

    filter_params = {}
    for key, value in query_parameters.dict().items():
        if value and key not in ['q', 'p', 'l', 'tags']:
            if key in ['lastUpdatedFrom', 'lastUpdatedTo', 'singleChapter', 'completionStatus']:
                filter_params[key] = value
            else:
                filter_params[key] = int(value)

    query = str(query_parameters.q)
    page = query_parameters.p
    limit = query_parameters.l
    
    # print(query)
    # print(tags)
    # print(filter_params)

    # results_query = await cached_search(query_parameters.q, tags, {'kudosCountFrom', 300})
    # results_query = search_engine_client.query("harry", [], {'kudosCountFrom': 300})
    results_query = search_engine_client.query(query, tags, filter_params)
    # print(str(query) == "harry potter")
    # results_query = search_engine_client.query('"harry potter"', [], {})

    end = page * limit
    start = end - limit

    if start > len(results_query):
        results_paginated = []
    elif end > len(results_query):
        results_paginated = results_query[start:]
    else:
        results_paginated = results_query[start:end]
    return JSONResponse(content=results_paginated, status_code=200)


@app.get("/autocomplete")
async def read_pair(prefix: str):
    print(prefix)
    # if not prefix or prefix == "":
    #     completions = {}
    # elif len(prefix.strip()) >= 2:
    #     completions = search_engine_client.autocomplete(prefix)
    # else:
    #     completions = {}
    completions = search_engine_client.autocomplete(prefix)
    return JSONResponse(content=completions, status_code=200)

# ===============================================================
# ========================== CACHING ============================
# ===============================================================
# See https://github.com/aio-libs/aiocache#usage

query_results_cache = Cache(Cache.MEMORY)
ttl = 60 * 10  # How long we preserve query results for, in s
serialiser = PickleSerializer()


@cached(ttl=ttl, cache=Cache.MEMORY, serializer=serialiser)
async def cached_search(query: str, tags, filter_params: any):
    """
    Cache results returned from the search engine client.
    """
    return search_engine_client.query(query, tags, filter_params)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(
            "Usage: python FrontEndApi.py <ip> <port> <se_server_ip> <se_server_port>"
        )
        sys.exit(1)

    ip = sys.argv[1]
    print("IP:", ip)
    port = int(sys.argv[2])
    print("Port:", port)

    se_ip = sys.argv[3]
    print("SE IP:", se_ip)
    se_port = int(sys.argv[4])
    print("SE Port:", se_port)

    search_engine_client = SearchEngineAPIClient(se_ip, se_port)

    uvicorn.run(app, host=ip, port=port)
