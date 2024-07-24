import streamlit as st

from retriever import Retriever

default_model = "krlvi/sentence-msmarco-bert-base-dot-v5-nlpl-code_search_net"

st.set_page_config(layout="wide")
st.title("Chat with your code")
user_repo = st.text_input("Github Link to a public codebase", placeholder="Enter Link to a public codebase")

if user_repo:
    # Load the GitHub Repo
    retriever = Retriever(user_repo, default_model)
    st.write("Your repo has been cloned")

    # Chunk and Create Vector DB
    st.write("Parsing Repository content and creating VectorDB. This may take a while..")
    retriever.load_db()
    st.write("Done Loading. Ready to answer your questions")

    # Maintain chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.code(message["content"])

    # Accept user input
    if prompt := st.chat_input("Type your question here."):

        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        st.write("Here are the top 3 results")
        # Display assistant response in chat message container
        response = retriever.retrieve_results(prompt)

        cols = st.columns(len(response), vertical_alignment="top")

        for i in range(len(response)):
            with cols[i]:
                st.text("Result {}: {}".format(i+1, response[i]["file_name"]))
                with st.chat_message("assistant"):
                    st.code(response[i]["page_content"])

        st.session_state.messages.append({"role": "assistant", "content": response})
