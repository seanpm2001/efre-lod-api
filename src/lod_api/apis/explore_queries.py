from copy import deepcopy

_aggs = {
        "topAuthors": {
            "terms": {
                "field": 'contributor.@id.keyword',
                "size": 10
                }
            },
        "datePublished": {
            "date_histogram": {
                "field": "datePublished.dateParsed",
                "calendar_interval": "year",
                "min_doc_count": 1
                }
            },
        "mentions": {
            "terms": {
                "field": "mentions.@id.keyword",
                "size": 10
                }
            },
        "genres": {
            "terms": {
                "field": 'genre.Text.keyword',
                "size": 20
                }
            },
        "topMentionedTopics": {
            "terms": {
                "field": 'mentions.@id.keyword',
                "include": '.*topics.*',
                "size": 10
                }
            },
        "topContributors": {
            "terms": {
                "field": 'contributor.@id.keyword',
                "size": 10
                }
            }
        }

_sort_aggs = ["_score",
             {
                 "datePublished.dateParsed": {
                     "order": "desc"
                     }
                 }
             ]

_fields_aggs = [
                "preferredName^2",
                "description",
                "mentions.preferredName^2",
                "isPartOf.name",
                "about.name",
                "about.keywords",
                'description'
               ]

### generic topicsearch query ###
#
#
def topic_query(query, q_size, q_fields, q_excludes, q_from=0):
    # TOOD: multi_match types best_fields, most_fields, cross_fields, phrase, phrase_prefix, bool_prefix
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-multi-match-query.html
    # multi_match:
    #   query,
    #   fields: ['*'],
    #
    # type: 'most_fields'
    # }
    return {
        'size': q_size,
        'from': q_from,
        '_source': q_excludes,
        'query': {
            "multi_match": {
                'query':  query,
                'fields': q_fields,
                'type': 'phrase'
                }
            }
        }

### phraseMatch queries ###
#
#
def topic_aggs_query_phraseMatch(query, filter1=None):
    """
    Creates elasticsearch query for aggregations based on a simple
    phrase search for different subjects contained in `query`.
    :param list query
    :param str filter1 - filter query that is used for author names

    :returns: dict elasticsearch query body
    """
    if isinstance(query, str):
        subjects = [query]
    elif isinstance(query, list):
        subjects = query
    else:
        raise Exception("query should be of type str or list")

    if filter1:
        author_filter = [{
                "multi_match": {
                    "fields": [
                        "title.responsibilityStatement.keyword",
                        "contributor.name.keyword"
                        ],
                    "query": filter1
                    }
                }]
    else:
        author_filter = []

    return {
        "size": 15,
        "sort": _sort_aggs,
        "query": {
            "bool": {
                "must" : [
                    {
                        "multi_match": {
                            "query": subj,
                            "fields": _fields_aggs,
                            "type": "phrase"
                            }
                        }
                    for subj in subjects],
                "filter": author_filter
                }
            },
        "aggs": _aggs
        }

def topic_maggs_query_phraseMatch(subjects):
    """
    Creates a aggregation query "topicAM" which produces a
    adjacency matrix with different subject correlations in its
    fields.
    :param list subjects - list of subjects

    :returns: tuple of aggregation name together with aggregation query
    to use with elasticsearch
    """

    query = {
            "size": 0,
            "aggs": {
                "topicAM": {
                    "adjacency_matrix": {
                        "filters": {
                            subj: {
                                "multi_match": {
                                    "query": subj,
                                    "fields": [
                                        "preferredName",
                                        "description",
                                        "mentions.preferredName",
                                        "isPartOf.name",
                                        "about.name",
                                        "about.keywords"
                                    ],
                                    "type": "phrase"
                                }
                            }
                            for subj in subjects
                        }
                    }
                }
            }
        }
    return query


### topicMatch queries ###
#
#
def topic_aggs_query_topicMatch(query, filter1=None):
    """
    Creates elasticsearch query for aggregations based on filter
    restricting the query to specific topic names. Query subjects are
    given in `query` parameter.
    :param list query
    :param str filter1 - filter query that is used for author names

    :returns: dict elasticsearch query body
    """
    if isinstance(query, str):
        subjects = [query]
    elif isinstance(query, list):
        subjects = query
    else:
        raise Exception("query should be of type str or list")

    if filter1:
        author_filter = [{
                "multi_match": {
                    "fields": [
                        "title.responsibilityStatement.keyword",
                        "contributor.name.keyword"
                        ],
                    "query": filter1
                    }
                }]
    else:
        author_filter = []

    subject_filters = [{
            "term": {
                'mentions.name.keyword': subj
                }
            }
            for subj in subjects
        ]


    return {
        "size": 15,
        "sort": _sort_aggs,
        "query": {
            "bool": {
                "must" : [
                    {
                        "multi_match": {
                            "query": subj,
                            "fields": _fields_aggs,
                            "type": "phrase"
                            }
                        }
                    for subj in subjects],
                "filter": subject_filters + author_filter
                }
            },
        "aggs": _aggs
        }

def topic_maggs_query_topicMatch(subjects):
    """
    Creates a aggregation query "topicAM" which produces a
    adjacency matrix with different subject correlations in its
    fields.
    :param list subjects - list of subjects

    :returns: tuple of aggregation name together with aggregation query
    to use with elasticsearch
    """
    query = {
            "size": 0,
            "aggs": {
                "topicAM": {
                    "adjacency_matrix": {
                        "filters": {
                            subj: {
                                "terms": {
                                    "mentions.name.keyword": [subj]
                                }
                            }
                            for subj in subjects
                        }
                    }
                }
            }
        }
    return query

def topic_resource_mentionCount(topic_id):
    return {
        'size': 0,
        'query': {
            'term': {
                'mentions.@id.keyword': topic_id
                }
            }
        }
