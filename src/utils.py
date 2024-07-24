from enum import Enum
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.storage.docstore import BaseDocumentStore
from llama_index.core.schema import NodeWithScore
from typing import List, Optional
from llama_index.core import QueryBundle
import os

EXCLUDE_DIRS = ['__pycache__', '.venv', '.git', '.idea', 'venv', 'env', 'node_modules', 'dist', 'build', '.vscode',
                '.github', '.gitlab']

ALLOW_FILES = [".c",      # C
    ".cpp",    # C++
    ".cs",     # C#
    ".cbl", ".cob", # COBOL
    ".ex", ".exs",  # Elixir
    ".go",     # Go
    ".java",   # Java
    ".js",     # JavaScript
    ".kt",     # Kotlin
    ".lua",    # Lua
    ".pl",     # Perl
    ".py",     # Python
    ".rb",     # Ruby
    ".rs",     # Rust
    ".scala",  # Scala
    ".ts"      # TypeScript,
    ".md"      # Markdown
]


class ProgrammingLanguages(Enum):
    CPP = 'cpp'
    GO = 'go'
    JAVA = 'java'
    KOTLIN = 'kotlin'
    JS = 'js'
    TS = 'ts'
    PHP = 'php'
    PROTO = 'proto'
    PYTHON = 'python'
    RST = 'rst'
    RUBY = 'ruby'
    RUST = 'rust'
    SCALA = 'scala'
    SWIFT = 'swift'
    MARKDOWN = 'markdown'
    LATEX = 'latex'
    HTML = 'html'
    SOL = 'sol'
    CSHARP = 'csharp'
    COBOL = 'cobol'
    C = 'c'
    LUA = 'lua'
    PERL = 'perl'
    HASKELL = 'haskell'
    ELIXIR = 'elixir'


# mapping to convert file extension to Langchain Languages Enum
file_extension_mapping = {
    ".c": ProgrammingLanguages.C.value,
    ".cpp": ProgrammingLanguages.CPP.value,
    ".cs": ProgrammingLanguages.CSHARP.value,
    ".cbl": ProgrammingLanguages.COBOL.value,
    ".cob": ProgrammingLanguages.COBOL.value,
    ".ex": ProgrammingLanguages.ELIXIR.value,
    ".exs": ProgrammingLanguages.ELIXIR.value,
    ".go": ProgrammingLanguages.GO.value,
    ".java": ProgrammingLanguages.JAVA.value,
    ".js": ProgrammingLanguages.JS.value,
    ".kt": ProgrammingLanguages.KOTLIN.value,
    ".lua": ProgrammingLanguages.LUA.value,
    ".pl": ProgrammingLanguages.PERL.value,
    ".py": ProgrammingLanguages.PYTHON.value,
    ".rb": ProgrammingLanguages.RUBY.value,
    ".rs": ProgrammingLanguages.RUST.value,
    ".scala": ProgrammingLanguages.SCALA.value,
    ".ts": ProgrammingLanguages.TS.value
}

# Addd more for specific languages
EXCLUDE_FILES = ['requirements.txt', 'package.json', 'package-lock.json', 'yarn.lock', '__init__.py', 'Dockerfile',
'.flake8', '.gitignore', '.pre-commit-config.yaml', 'pyproject.toml', 'setup.cfg', 'setup.py', 'tox.ini', 'Jenkinsfile',]


class CustomNodePostProcessor(BaseNodePostprocessor):
    docstore: BaseDocumentStore

    def _postprocess_nodes(self, nodes: List[NodeWithScore], query_bundle: Optional[QueryBundle]) -> List[NodeWithScore]:
        augmented_nodes: List[NodeWithScore] = []
        for n in nodes:
            if len(n.node.text) < 150:
                try:
                    next_node_id = n.node.next_node.node_id
                    next_node_text = self.docstore.get_node(next_node_id).text
                    n.node.text = n.node.text + "\n" + next_node_text
                except:
                    pass
            augmented_nodes.append(n)
        return augmented_nodes


def get_readme(repo_path: str):
    try:
        with open(os.path.join(repo_path, "README.md"), "r") as f:
            return f.read()
    except:
        return None