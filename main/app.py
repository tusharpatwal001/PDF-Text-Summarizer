import streamlit as st
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama.chat_models import ChatOllama
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from PyPDF2 import PdfReader


def get_pdf_text(pdf):
    text = ""
    for pdf in pdf:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


def get_text_chunks(docs):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(docs)
    return chunks


def get_vector_store(chunks):
    embeddings = OllamaEmbeddings(model="mxbai-embed-large:latest")
    vectorstore = FAISS.from_texts(chunks, embedding=embeddings)
    vectorstore.save_local("faiss_index")


def get_conversational_chain():

    prompt_template = """
        Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """

    model = ChatOllama(model="gemma3:1b", temperature=0.3)
    prompt = PromptTemplate(template=prompt_template,
                            input_variables=['context', 'question'])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

    return chain


def user_input(question):
    embeddings = OllamaEmbeddings(model="mxbai-embed-large:latest")

    new_db = FAISS.load_local(
        "faiss_index", embeddings=embeddings, allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(question)
    chain = get_conversational_chain()

    response = chain(
        {"input_documents": docs, "question": question},
        return_only_outputs=True
    )
    print(response)
    st.write("Reply: \n", response['output_text'])


def main():
    st.set_page_config("Chat PDF")
    st.header("Chat with PDF using Gemma3")

    user_question = st.text_input("Ask a Question from the PDF Files")

    if user_question:
        user_input(user_question)

    with st.sidebar:
        st.title("Menu:")
        pdf_docs = st.file_uploader(
            "Upload your PDF Files and Click on the Submit & Process Button", accept_multiple_files=True)
        if st.button("Submit & Process"):
            with st.spinner("Processing..."):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks)
                st.success("Done")


if __name__ == "__main__":
    main()
