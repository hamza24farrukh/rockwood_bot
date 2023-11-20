import os
import io
import re
import openai

from pypdf import PdfReader, PdfWriter
from flask import jsonify

from azure.core.credentials import AzureKeyCredential
from config.ExternalConfiguration import ExternalConfiguration


from azure.search.documents.indexes.models import SearchIndex
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes import *
from azure.storage.blob import BlobServiceClient

from azure.search.documents.indexes.models import ( 
    ExhaustiveKnnVectorSearchAlgorithmConfiguration,
    ExhaustiveKnnParameters,
    SearchIndex,  
    SearchField,  
    SearchFieldDataType,  
    SimpleField,  
    SearchableField,  
    SearchIndex,  
    SemanticConfiguration,  
    PrioritizedFields,  
    SemanticField,  
    SearchField,  
    SemanticSettings,  
    VectorSearch,  
    HnswVectorSearchAlgorithmConfiguration,
    HnswParameters,  
    VectorSearch,
    VectorSearchAlgorithmConfiguration,
    VectorSearchAlgorithmKind,
    VectorSearchProfile,
    VectorSearchVectorizer,
    VectorSearchVectorizerKind,
    AzureOpenAIParameters,
    AzureOpenAIVectorizer,
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswVectorSearchAlgorithmConfiguration,
    ExhaustiveKnnVectorSearchAlgorithmConfiguration,
    ExhaustiveKnnParameters,
    SearchIndex,  
    SearchField,  
    SearchFieldDataType,  
    SimpleField,  
    SearchableField,  
    SearchIndex,  
    SemanticConfiguration,  
    PrioritizedFields,  
    SemanticField,  
    SearchField,  
    SemanticSettings, 
    VectorSearch,  
    HnswVectorSearchAlgorithmConfiguration,
    HnswParameters,  
    VectorSearch,
    VectorSearchAlgorithmKind,
    VectorSearchProfile,
    AzureOpenAIParameters,
    AzureOpenAIVectorizer,
)

config = ExternalConfiguration()


AZURE_STORAGE_ACCOUNT = config.AZURE_STORAGE_ACCOUNT
AZURE_STORAGE_CONTAINER = "content-test" or config.AZURE_STORAGE_CONTAINER
azure_credential = AzureKeyCredential(config.AZURE_SEARCH_SERVICE_KEY)
AZURE_SEARCH_SERVICE = config.AZURE_SEARCH_SERVICE




MAX_SECTION_LENGTH = 1000
SENTENCE_SEARCH_LIMIT = 100
SECTION_OVERLAP = 100

class FileUploader:
    def UploadFileToAzureSearch(self,uploadedFile, searchIndex, resourceId):
        print('Index Name: ', searchIndex)
        reader = PdfReader(uploadedFile)
        pages = len(reader.pages)
        FileUploader.upload_blobs(FileUploader, uploadedFile)
        page_maps = self.get_document_text(reader)
        sections = self.create_sections(FileUploader,os.path.basename(uploadedFile.filename), page_maps, resourceId)
        print('Sections: ', sections)
        self.index_sections(FileUploader,os.path.basename(uploadedFile.filename), sections, searchIndex)
        print('Number of pages: ', pages)
        return jsonify({ "success":True, "message":"Sections created successfully.", "sections":str(sections) })
    
    def UploadWebpageToAzureSearch(self,webpage, searchIndex, resourceId):
        print('Index Name: ', searchIndex)
    
        page_maps = self.get_webpage_text(webpage['extracted_content'])
        sections = self.create_sections(FileUploader,os.path.basename(webpage['url']), page_maps, resourceId)
        print('Sections: ', sections)
        self.index_sections(FileUploader,os.path.basename(webpage['url']), sections, searchIndex)
        return jsonify({ "success":True, "message":" webpage Sections created successfully.", "sections":str(sections) })

    def upload_blobs(self, file):
        blob_service = BlobServiceClient(account_url=f"https://{AZURE_STORAGE_ACCOUNT}.blob.core.windows.net", credential=config.AZURE_STORAGE_ACCOUNT_KEY)
        blob_container = blob_service.get_container_client(AZURE_STORAGE_CONTAINER)
        if not blob_container.exists():
            blob_container.create_container()

        # if file is PDF split into pages and upload each page as a separate blob
        if os.path.splitext(file.filename)[1].lower() == ".pdf":
            reader = PdfReader(file)
            pages = reader.pages
            for i in range(len(pages)):
                blob_name = self.blob_name_from_file_page(file.filename, i)
                f = io.BytesIO()
                writer = PdfWriter()
                writer.add_page(pages[i])
                writer.write(f)
                f.seek(0)
                uploaded_blob = blob_container.upload_blob(blob_name, f, overwrite=True)
                print(uploaded_blob.account_name + "\\" + uploaded_blob.container_name + "\\" +uploaded_blob.blob_name)
        else:
            blob_name = self.blob_name_from_file_page(file.filename)
            with open(file,"rb") as data:
                print("Bytes: ", "".join(data))
                uploaded_blob = blob_container.upload_blob(blob_name, data, overwrite=True)
                print(uploaded_blob.blob_name)

    def get_document_text(reader):
        offset = 0
        page_map = []
        #reader = PdfReader(file)
        pages = reader.pages
        for page_num, p in enumerate(pages):
            page_text = p.extract_text()
            page_map.append((page_num, offset, page_text))
            offset += len(page_text)
        return page_map
    
    def get_webpage_text(webpage_text):
        offset = 0
        page_map = []
        # Split the webpage text into pages based on some criteria (e.g., headings or page separators)
        # Here, we'll assume that pages are separated by the '<page_break>' string.
        pages = webpage_text.split('<page_break>')
        
        for page_num, page_text in enumerate(pages):
            # Calculate the length of the page text
            page_length = len(page_text)
            page_map.append((page_num, offset, page_text))
            offset += page_length
        return page_map


    def split_text(page_map):
        # Define lists of characters that denote the endings of sentences and word breaks.
        SENTENCE_ENDINGS = [".", "!", "?"]
        WORDS_BREAKS = [",", ";", ":", " ", "(", ")", "[", "]", "{", "}", "\t", "\n"]

        # Define a helper function to find the page based on an offset within page_map.
        def find_page(offset):
            l = len(page_map)
            for i in range(l - 1):
                if offset >= page_map[i][1] and offset < page_map[i + 1][1]:
                    return i
            return l - 1

        # Concatenate all text from page_map into a single string.
        all_text = "".join(p[2] for p in page_map)
        length = len(all_text)
        start = 0
        end = length

        # Process the text in sections.
        while start + SECTION_OVERLAP < length:
            last_word = -1
            end = start + MAX_SECTION_LENGTH

            # Adjust 'end' based on sentence endings to form coherent sections.
            if end > length:
                end = length
            else:
                # Try to find the end of a sentence.
                while end < length and (end - start - MAX_SECTION_LENGTH) < SENTENCE_SEARCH_LIMIT and all_text[end] not in SENTENCE_ENDINGS:
                    if all_text[end] in WORDS_BREAKS:
                        last_word = end
                    end += 1
                if end < length and all_text[end] not in SENTENCE_ENDINGS and last_word > 0:
                    end = last_word  # Ensure ending at a whole word

            if end < length:
                end += 1

            # Try to find the start of the sentence or a whole word boundary.
            last_word = -1
            while start > 0 and start > end - MAX_SECTION_LENGTH - 2 * SENTENCE_SEARCH_LIMIT and all_text[start] not in SENTENCE_ENDINGS:
                if all_text[start] in WORDS_BREAKS:
                    last_word = start
                start -= 1
            if all_text[start] not in SENTENCE_ENDINGS and last_word > 0:
                start = last_word

            if start > 0:
                start += 1

            # Extract a section of text based on the calculated 'start' and 'end'.
            section_text = all_text[start:end]

            # Yield the section text along with the page it belongs to (determined by 'find_page').
            yield (section_text, find_page(start))

            # Handle special cases related to tables in the section text.
            last_table_start = section_text.rfind("<table")
            if (last_table_start > 2 * SENTENCE_SEARCH_LIMIT and last_table_start > section_text.rfind("</table")):
                # If the section ends with an unclosed table, adjust the start to include the table.
                # Note: Some checks are in place to avoid infinite loops.
                start = min(end - SECTION_OVERLAP, start + last_table_start)
            else:
                start = end - SECTION_OVERLAP

        if start + SECTION_OVERLAP < end:
            # Yield the remaining text section and its corresponding page.
            yield (all_text[start:end], find_page(start))


    def create_sections(self, filename, page_map, resourceId):
        for i, (section, pagenum) in enumerate(self.split_text(page_map)):
            yield {
                "id": re.sub("[^0-9a-zA-Z_-]","_",f"{filename}-{i}"),
                "content": section,
                "category": "",
                "sourcepage": self.blob_name_from_file_page(filename, pagenum),
                "sourcefile": filename,
                "resourceId": str(resourceId),
                "embedding": self.compute_embedding(section)
            }

    def blob_name_from_file_page(filename, page = 0):
        if os.path.splitext(filename)[1].lower() == ".pdf":
            return os.path.splitext(os.path.basename(filename))[0] + f"-{page}" + ".pdf"
        else:
            return os.path.basename(filename)


    def create_search_index(index_name): 
        print(f"Ensuring search index {index_name} exists")
        index_client = SearchIndexClient(endpoint=f"https://{AZURE_SEARCH_SERVICE}.search.windows.net/",
                                        credential=azure_credential)
        if str(index_name) not in list(index_client.list_index_names()):
                fields=[
                    SimpleField(name="id", type="Edm.String", key=True),
                    SearchableField(name="content", type="Edm.String", analyzer_name="en.microsoft"),
                    SimpleField(name="category", type="Edm.String", filterable=True, facetable=True),
                    SimpleField(name="sourcepage", type="Edm.String", filterable=True, facetable=True),
                    SimpleField(name="sourcefile", type="Edm.String", filterable=True, facetable=True),
                    SimpleField(name="resourceId", type="Edm.String", filterable=True, facetable=True),
                    SearchField(
                        name="embedding",
                        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        hidden=False,
                        searchable=True,
                        vector_search_dimensions=1536,
                        vector_search_profile="myHnswProfile"
                        
                    )
                ]
                # Configure the vector search configuration  
                vector_search = VectorSearch(
                algorithms=[
                    HnswVectorSearchAlgorithmConfiguration(
                        name="myHnsw",
                        kind=VectorSearchAlgorithmKind.HNSW,
                        parameters=HnswParameters(
                            m=4,
                            ef_construction=400,
                            ef_search=500,
                            metric="cosine"
                        )
                    ),
                    ExhaustiveKnnVectorSearchAlgorithmConfiguration(
                        name="myExhaustiveKnn",
                        kind=VectorSearchAlgorithmKind.EXHAUSTIVE_KNN,
                        parameters=ExhaustiveKnnParameters(
                            metric="cosine"
                        )
                    )
                ],
                profiles=[
                    VectorSearchProfile(
                        name="myHnswProfile",
                        algorithm="myHnsw",
                    ),
                    VectorSearchProfile(
                        name="myExhaustiveKnnProfile",
                        algorithm="myExhaustiveKnn",
                    )
                ],

            )

                semantic_config = SemanticConfiguration(
                    name="my-semantic-config",
                    prioritized_fields=PrioritizedFields(
                        title_field=None,
                        prioritized_keywords_fields=[SemanticField(field_name="content")],
                    )
                )

                # Create the semantic settings with the configuration
                semantic_settings = SemanticSettings(configurations=[semantic_config])

                # Create the search index with the semantic settings
                index = SearchIndex(name=index_name, fields=fields,vector_search=vector_search, semantic_settings=semantic_settings)
                print(f"Creating {index_name} search index")
                index_client.create_index(index)
                return f'Index Created with name: {index}'
        else:
            print(f"Search index {index_name} already exists")
            return f'Search index {index_name} already exists'
        

    def index_sections(self, filename, sections, index):
        self.create_search_index(index)
       
        search_client = SearchClient(endpoint=f"https://{AZURE_SEARCH_SERVICE}.search.windows.net/",
                                        index_name=index,
                                        credential=azure_credential)

        i = 0
        batch = []
        for s in sections:
            batch.append(s)
            i += 1
            if i % 1000 == 0:
                results = search_client.upload_documents(documents=batch)
                succeeded = sum([1 for r in results if r.succeeded])
                batch = []

        if len(batch) > 0:
            results = search_client.upload_documents(documents=batch)
            succeeded = sum([1 for r in results if r.succeeded])
            
        
    def compute_embedding(text):
        embedding_args = {"deployment_id": config.AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT}
        openai.api_type = config.AZURE_OPENAI_APITYPE
        openai.api_key = config.AZURE_OPENAI_APIKEY
        openai.api_base = config.AZURE_OPENAI_BASEURL
        openai.api_version = config.AZURE_OPENAI_VERSION
        return openai.Embedding.create(**embedding_args, model=config.AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT, input=text)["data"][0]["embedding"]

