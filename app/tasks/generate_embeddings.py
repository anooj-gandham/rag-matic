# app/generate_embeddings.py
from celery import shared_task
from app.models.files import File
from app.utils.embeddings import generate_embeddings, store_embeddings
from app.utils.parsers import parse_file_from_url
from app.utils.chunk_generator import generate_chunks
from config.celery import app


@app.task(queue="embeddings")
def process_file_for_embeddings(file_id):
    """
    Celery task to process a file and generate its embeddings.
    This task will be routed to the 'embedding_queue'.
    """
    try:
        file_instance = File.objects.get(id=file_id)
        texts, ext = parse_file_from_url(file_instance.url)
        MAX_TOKENS_PER_CHUNK = 800
        chunks = generate_chunks(texts, max_tokens=MAX_TOKENS_PER_CHUNK)
        embeddings = [generate_embeddings(chunk) for chunk in chunks]
        response = store_embeddings(str(file_instance.id), texts, embeddings)

        # Store UUID of embeddings stored in Weaviate.
        uuids_dict = response.uuids
        for key in uuids_dict.keys():
            uuids_dict[key] = str(uuids_dict[key])

        file_instance.weaviate_ids = uuids_dict
        file_instance.processed = True
        file_instance.save()

        return {
            "status": "SUCCESS",
            "file_id": str(file_instance.id),
            "weaviate_ids": uuids_dict
        }
        
        
    except File.DoesNotExist:
        # Optionally log or handle the error.
        pass
