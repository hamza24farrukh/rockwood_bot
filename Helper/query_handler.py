import os

class QueryHandler:
    def __init__(self, client):
        self.client = client

    def get_completion(self, prompt):
        response = self.client.completions.create(model=os.environ.get("AZURE_OPENAI_GPT_DEPLOYMENT"), prompt=prompt, max_tokens=15)
        return response.choices[0].text

    def rephrase_query(self, query):
        prompt = f"Rephrase the following query: \"{query}\""
        return self.get_completion(prompt)

