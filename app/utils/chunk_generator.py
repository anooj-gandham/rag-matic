import tiktoken

def split_text_into_chunks(text, max_tokens, encoding):
    """
    Splits a single text into chunks based on the max_tokens limit.

    Args:
        text (str): The text to split.
        max_tokens (int): The maximum number of tokens per chunk.
        encoding (tiktoken.Encoding): The tiktoken encoding to use.

    Returns:
        list: A list of text chunks.
    """
    tokens = encoding.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i + max_tokens]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)

    return chunks

def generate_chunks(texts, max_tokens, model_name="gpt-4o"):
    """
    Splits an array of texts into chunks based on the max_tokens limit.

    Args:
        texts (list): A list of text strings to process.
        max_tokens (int): The maximum number of tokens per chunk.
        model_name (str): The model name to determine the encoding. Default is "gpt-4o".

    Returns:
        list: A list of text chunks.
    """
    try:
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        print(f"Model '{model_name}' not found. Using 'o200k_base' encoding.")
        encoding = tiktoken.get_encoding("o200k_base")

    all_chunks = []
    for text in texts:
        if len(encoding.encode(text)) > max_tokens:
            chunks = split_text_into_chunks(text, max_tokens, encoding)
            all_chunks.extend(chunks)
        else:
            all_chunks.append(text)
    return all_chunks

if __name__ == '__main__':
    # Example usage:
    texts = [
        "This is a short sentence.",
        "This is a much longer sentence that will likely exceed the token limit when processed through the tokenizer, especially if the max_tokens limit is set relatively low."
    ]
    max_tokens = 10
    chunks = generate_chunks(texts, max_tokens)
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i + 1}: {chunk}\n")


