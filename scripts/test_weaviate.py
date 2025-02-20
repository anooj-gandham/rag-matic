import weaviate
import weaviate.classes as wvc
from weaviate.classes.query import MetadataQuery
import json
import numpy as np

# app/utils.py
from typing import List
import weaviate
from openai import OpenAI
import weaviate.classes as wvc
from weaviate.classes.query import MetadataQuery

# app/utils.py
from typing import List
import weaviate
from openai import OpenAI
import weaviate.classes as wvc
from weaviate.classes.query import MetadataQuery

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI as LangchainOpenAI


def generate_embeddings(text: str) -> List[float]:
    """
    Generate an embedding vector for the provided text using OpenAI's embedding API.

    This function calls the OpenAI embeddings endpoint with the "text-embedding-3-small" model
    and returns the embedding vector as a list of floats.

    Args:
        text (str): The input text to be embedded.

    Returns:
        List[float]: A list of float values representing the text embedding.
    """
    client = OpenAI()
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def uuid_to_weaviate_class(uuid_str: str) -> str:
    """
    Convert a UUID string into a valid Weaviate class name.
    
    Weaviate class names must be strings that start with a letter and contain only 
    alphanumeric characters (and underscores, if desired). This function removes
    hyphens from the UUID and, if the result does not start with a letter, prefixes it 
    with "Cls_".
    
    Args:
        uuid_str (str): The UUID string (e.g., "482a0ffb-a20f-4df8-bf84-7ab6a47be8e2").
        
    Returns:
        str: A valid Weaviate class name.
    """
    # Remove hyphens
    name = uuid_str.replace("-", "")
    
    # Ensure the name starts with an alphabet character.
    name = "Cls_" + name
        
    return name

def query_from_entries(query_text: str, collection_identifier: str, limit: int = 2) -> any:
    """
    Query a Weaviate collection for entries similar to the given text.

    Args:
        query_text (str): The text query to search for.
        collection_identifier (str): A string representing the collection name or a UUID.
            If this is a UUID string, it will be converted into a valid Weaviate class name.
        limit (int, optional): The maximum number of results to return. Defaults to 2.

    Returns:
        Any: The response from Weaviate containing matching objects and additional metadata.
    """
    # Connect to the local Weaviate instance.
    wv_client = weaviate.connect_to_local()

    # Convert collection_identifier to a valid collection name if necessary.
    # If your collection name is already a valid string (e.g., "Files"), you may omit this conversion.
    valid_collection_name = uuid_to_weaviate_class(collection_identifier)

    # Generate the embedding for the query text.
    query_vector = generate_embeddings(query_text)

    # Retrieve the collection.
    collection = wv_client.collections.get(valid_collection_name)

    # Execute the near-vector query.
    response = collection.query.near_vector(
        near_vector=query_vector,
        limit=limit,
        return_metadata=MetadataQuery(distance=True)
    )

    # Close the connection.
    wv_client.close()

    return response

def main():
    # Connect to the local Weaviate instance.
    client = weaviate.connect_to_local()

    # Try to retrieve the "Question_1" collection.
    try:
        questions = client.collections.get("Question_1")
    except Exception:
        questions = client.collections.create(
            "Question_1",
            vectorizer_config=wvc.config.Configure.Vectorizer.none(),
        )

    # Prepare a few test entries with dummy vectors.
    question_objs = []
    for i in range(3):
        question_objs.append(
            wvc.data.DataObject(
                properties={
                    "answer": "This .",
                    "question": "csdcsdc svc dfv df",
                    "category": f"{i}",
                },
                vector=np.random.rand(34).tolist()
            )
        )

    # Insert the entries into the collection.
    ret = questions.data.insert_many(question_objs)
    uuids_dict = ret.uuids
    for key in uuids_dict.keys():
        uuids_dict[key] = str(uuids_dict[key])
    # import pdb; pdb.set_trace()

    # print(response)


    responses = questions.query.near_vector(
        near_vector=np.random.rand(34).tolist(),
        limit=4,
        return_metadata=MetadataQuery(distance=True)

    )

    import pdb; pdb.set_trace()



    # Close the client connection
    client.close()

def test_query():

    try:
        query = "What potential applications do these time-domain constraints have in practical areas such as electromagnetic compatibility, transient protection (e.g., lightning strikes), and high-speed electronic switching circuits?"
        response = query_from_entries(query, "e5878710-944d-409c-8ba7-fa45e1c877c5", 4)

        context = ""
        for object in response.objects:
            context += object.properties["text"].replace("\n", "") + "\n"

        query = query + "\n" + context

        # Initialize the OpenAI model
        llm = LangchainOpenAI(model="gpt-4o", temperature=0.7)
        template = PromptTemplate.from_template("Generate the response in a <></> tag with headings and subsections. {query}: {content}")
        prompt = template.format(query=query, content=context)
        response = llm.invoke(prompt)
        # import pdb; pdb.set_trace()
        print(response.content)

    except Exception as e:
        print(e)
        raise e

        

if __name__ == "__main__":
    test_query()
