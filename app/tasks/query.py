# app/tasks/query.py
from celery import shared_task
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from app.models.files import File
from app.utils.embeddings import query_from_entries
from config.celery import app


@app.task(queue="queries")
def generate_response(query, file_id):
    """
    Celery task to process a file and generate its embeddings.
    This task will be routed to the 'embedding_queue'.
    """
    try:
        file_instance = File.objects.get(id=file_id)
        response = query_from_entries(query, str(file_instance.id), limit=3)
        context = ""
        for object in response.objects:
            context += object.properties["text"].replace("\n", "") + "\n"

        query = query + "\n" + context

        # Initialize the OpenAI model
        llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        template = PromptTemplate.from_template(
            "Generate the response in a <></> tag with headings and subsections. {query}: {content}"
        )
        prompt = template.format(query=query, content=context)
        response = llm.invoke(prompt)
        return response.content.replace("\n", "").replace("```html", "").replace("```", "")

        
    except File.DoesNotExist:
        # Optionally log or handle the error.
        pass