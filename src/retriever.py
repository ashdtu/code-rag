import git
import os
import torch
from typing import List, Dict, Tuple
from pathlib import Path
from utils import EXCLUDE_DIRS, EXCLUDE_FILES, file_extension_mapping
from tqdm import tqdm as tqdm
from llama_index.core.node_parser import CodeSplitter
from llama_index.readers.file import FlatReader
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import Settings
from llama_index.core import StorageContext
from llama_index.core import VectorStoreIndex
from utils import CustomNodePostProcessor
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.schema import BaseNode


class Retriever:
    """ "
    The Retriever class handles all the logic logic for Retrieval of code snippets from a given GitHub repository.
    """

    def __init__(
        self,
        git_link: str,
        model_name: str = "krlvi/sentence-msmarco-bert-base-dot-v5-nlpl-code_search_net",
    ) -> None:
        """
        Initialize the Retriever class with the given GitHub repository link and the embedding model name.
        :param git_link:
        :param model_name:
        """

        self.git_link = git_link
        last_name = self.git_link.split("/")[-1]
        self.base_save_path = "../data/"
        if not os.path.exists(self.base_save_path):
            os.makedirs(self.base_save_path)
        self.clone_path = os.path.join(self.base_save_path, last_name.split(".")[0])
        self.clone_repo()
        self.model_name = model_name
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = HuggingFaceEmbedding(model_name=self.model_name, device=device)
        self.vector_index = None
        Settings.chunk_size = 1500
        Settings.embed_model = self.model
        Settings.llm = None

    def clone_repo(self):
        if not os.path.exists(self.clone_path):
            git.Repo.clone_from(self.git_link, self.clone_path)

    def extract_chunks(self) -> Tuple[List[BaseNode], SimpleDocumentStore]:
        """ "
        Parse documents from the repo and creates chunks for the Vector Store.
        """
        root_dir = self.clone_path

        chunked_nodes = []
        doc_store = SimpleDocumentStore()

        for dirpath, dirnames, filenames in tqdm(os.walk(root_dir)):
            if dirnames in EXCLUDE_DIRS:
                continue
            for file in filenames:
                if file in EXCLUDE_FILES:
                    continue
                file_extension = os.path.splitext(file)[1]
                if file_extension in file_extension_mapping.keys():
                    try:
                        doc = FlatReader().load_data(Path(os.path.join(dirpath, file)))

                        splitter = CodeSplitter(
                            language=file_extension_mapping[file_extension],
                            chunk_lines=40,
                            chunk_lines_overlap=15,
                            max_chars=1500,
                        )

                        nodes = splitter.get_nodes_from_documents(doc)
                        chunked_nodes.extend(nodes)
                        doc_store.add_documents(nodes)
                    except Exception as e:
                        print(f"Error reading file {file}: {e}")
                        pass
        print("Total number of chunks: ", len(chunked_nodes))
        return chunked_nodes, doc_store

    def load_db(self):
        """
        Load the Vector Store from persistent storage if it exists, else create a new one from chunks.
        """

        store_path = os.path.join(
            self.base_save_path,
            f"{self.clone_path.split('/')[-1]}_{self.model_name.split('/')[-1]}",
        )
        if os.path.exists(store_path):
            if self.vector_index is None:
                db = chromadb.PersistentClient(path=store_path)
                chroma_collection = db.get_or_create_collection("chroma_collection")
                vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
                self.doc_store = SimpleDocumentStore().from_persist_path(
                    store_path + "/docstore"
                )
                self.vector_index = VectorStoreIndex.from_vector_store(
                    vector_store,
                    embed_model=self.model,
                )

                self.node_postprocessor = CustomNodePostProcessor(
                    docstore=self.doc_store
                )
                self.query_engine = self.vector_index.as_query_engine(
                    llm=None,
                    similarity_top_k=3,
                    node_postprocessors=[self.node_postprocessor],
                    response_mode="no_text",
                )
        else:
            doc_chunks, doc_store = self.extract_chunks()
            db = chromadb.PersistentClient(path=store_path)
            chroma_collection = db.get_or_create_collection("chroma_collection")
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)

            doc_store.persist(persist_path=store_path + "/docstore")
            self.vector_index = VectorStoreIndex(
                doc_chunks, storage_context=storage_context, embed_model=self.model
            )
            self.node_postprocessor = CustomNodePostProcessor(docstore=doc_store)
            self.query_engine = self.vector_index.as_query_engine(
                llm=None,
                similarity_top_k=3,
                node_postprocessors=[self.node_postprocessor],
                response_mode="no_text",
            )

    def retrieve_results(self, query: str) -> List[Dict]:
        """
        Retrieve the top 3 code snippets for the given query.
        :param query: string
        :return: Dict: Containing the code snippet and the source filename
        """
        response = self.query_engine.query(query)
        response_texts = []
        for node in response.source_nodes:
            response_texts.append(
                {"page_content": node.text, "file_name": node.metadata["filename"]}
            )

        return response_texts
