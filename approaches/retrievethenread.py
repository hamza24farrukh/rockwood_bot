import sys
import os
import openai
from MicroserviceServer.approaches.approach import Approach
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType
from MicroserviceServer.helpers.text import nonewlines
from flask import Flask, session
import jwt
import requests
import logging
from MicroserviceServer.helpers.prompthelper import prompthelper
from config.ExternalConfiguration import ExternalConfiguration
from MicroserviceServer.OpenAIDocSearch.FileUploader import FileUploader
from azure.search.documents.models import (
    QueryType,
    RawVectorQuery,
    QueryLanguage,
    QueryCaptionType,
    QueryAnswerType
)
from config.ExternalConfiguration import ExternalConfiguration
from azure.core.credentials import AzureKeyCredential


config = ExternalConfiguration()

azure_credential = AzureKeyCredential(config.AZURE_SEARCH_SERVICE_KEY)
AZURE_SEARCH_SERVICE = config.AZURE_SEARCH_SERVICE
EID_HASACCESS_URI = os.environ.get("EID_HASACCESS_URI") or ""

# Simple retrieve-then-read implementation, using the Cognitive Search and OpenAI APIs directly. It first retrieves
# top documents from search, then constructs a prompt with them, and then uses OpenAI to generate an completion 
# (answer) with that prompt.
class RetrieveThenReadApproach(Approach):

    def __init__(self, search_client: SearchClient, openai_deployment: str, sourcepage_field: str, content_field: str):
        self.search_client = search_client
        self.openai_deployment = openai_deployment
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field
        self.template = prompthelper().getprompt("AskPrompt")
        self.config = ExternalConfiguration()
        openai.api_type = self.config.AZURE_OPENAI_APITYPE
        openai.api_base = self.config.AZURE_OPENAI_BASEURL
        openai.api_key = self.config.AZURE_OPENAI_APIKEY
        openai.api_version = self.config.AZURE_OPENAI_VERSION

    def run(self, q: str, overrides: dict, token: str) -> any:
        use_semantic_captions = True if overrides.get("semantic_captions") else False
        top = overrides.get("top") or 3
        exclude_category = overrides.get("exclude_category") or None
        filter = "category ne '{}'".format(exclude_category.replace("'", "''")) if exclude_category else None

        # vector search
        query_vector = FileUploader.compute_embedding(q)
        vector_query = RawVectorQuery(vector=query_vector, k=3, fields="embedding")

        # hybrid semantic search
        if overrides.get("semantic_ranker"):
            r = self.search_client.search(search_text= q,
                                          vector_queries=[vector_query],
                                          select=["content", "category", "sourcepage","resourceId"],
                                          filter=filter,
                                          query_type=QueryType.SEMANTIC, 
                                          query_language=QueryLanguage.EN_US, 
                                          query_speller="lexicon", 
                                          semantic_configuration_name='my-semantic-config', 
                                          top=top, 
                                          query_caption=QueryCaptionType.EXTRACTIVE if use_semantic_captions else None,
                                          query_answer=QueryAnswerType.EXTRACTIVE)
        else:
            
            # hybrid Search which uses both keyword query and vectorized query
            r = self.search_client.search(search_text=q, vector_queries=[vector_query], select=["content", "category", "sourcepage","resourceId"], top=3) 

        authorizedDocs = []
        for doc in r:
            resId = doc["resourceId"]
            #print(resId)
            if True: 
                authorizedDocs.append(doc)
                #if has_access(token, resId)==True:
                    #authorizedDocs.append(doc)
                    #print("HAS ACCESS")
                #else:
                    #print("HAS NO ACCESS");

        if use_semantic_captions:
            results = [doc[self.sourcepage_field] + ": " + nonewlines(" . ".join([c.text for c in doc['@search.captions']])) for doc in authorizedDocs]
        else:
            results = [doc[self.sourcepage_field] + ": " + nonewlines(doc[self.content_field]) for doc in authorizedDocs]
        content = "\n".join(results)
        prompt = (overrides.get("prompt_template") or self.template).format(q=q, retrieved=content)
        completion = openai.Completion.create(
            engine=self.openai_deployment, 
            prompt=prompt, 
            temperature=overrides.get("temperature") or 0.4, 
            max_tokens=2048, 
            n=1, 
            stop=["\n"])
        
        response = {"answer": completion.choices[0].text}
        if overrides.get("data_points"):
            response["data_points"] = results
        if overrides.get("thoughts"):
            response["thoughts"] = f"Question:<br>{q}<br><br>Prompt:<br>" + prompt.replace('\n', '<br>')
        return response
        #return {"data_points": results, "answer": completion.choices[0].text, "thoughts": f"Question:<br>{q}<br><br>Prompt:<br>" + prompt.replace('\n', '<br>')}

