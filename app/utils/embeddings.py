# app/utils.py
import os
from typing import List
import weaviate
from openai import OpenAI
import weaviate.classes as wvc
from weaviate.classes.query import MetadataQuery


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

def store_embeddings(collection_name, texts, embeddings):
    """
    Store multiple texts and their corresponding embeddings in Weaviate.

    Args:
        collection: A Weaviate collection object (e.g., obtained via client.collections.get("YourClassName"))
        texts (list[str]): A list of texts to store.
        embeddings (list[list[float]]): A list of embedding vectors corresponding to the texts.

    Returns:
        The result of the batch insert operation from Weaviate.

    Note:
        Ensure that your collection's schema is configured with vectorizer set to "none" (or that the field is
        marked to skip vectorization) so that Weaviate uses your provided embeddings.
    """
    try:
        wv_client = weaviate.connect_to_local(
            host=os.getenv("WEAVIATE_HOST"),
            port=8080,
            grpc_port=50051,
        )
        collection_name = uuid_to_weaviate_class(collection_name)
        wv_client.collections.delete(collection_name)
        collection = wv_client.collections.create(
            name=collection_name,
            vectorizer_config=wvc.config.Configure.Vectorizer.none(),
            properties=[
                wvc.config.Property(name="text", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="index", data_type=wvc.config.DataType.INT)
            ]
        )

        # Build the data objects.
        data_objects = list()
        for i, text, embedding in zip(range(len(texts)), texts, embeddings):
            data_objects.append(
                wvc.data.DataObject(
                    properties={
                        "index": i,
                        "text": text
                    },
                    vector=embedding
                )
            )
        response = collection.data.insert_many(data_objects)
        wv_client.close()
        return response
    except Exception as e:
        print(f"Error storing embeddings: {e}")
        wv_client.close()
        raise e

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
    wv_client = weaviate.connect_to_local(
        host=os.getenv("WEAVIATE_HOST"),
        port=8080,
        grpc_port=50051,
    )

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