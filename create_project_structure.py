import os

project_structure = [
    "langgraph-agent/app/main.py",
    "langgraph-agent/app/api/router.py",
    "langgraph-agent/app/api/v1_agent.py",
    "langgraph-agent/app/agents/agent_manager.py",
    "langgraph-agent/app/agents/workflows.py",
    "langgraph-agent/app/tools/__init__.py",
    "langgraph-agent/app/tools/base.py",
    "langgraph-agent/app/tools/web_search.py",
    "langgraph-agent/app/tools/pdf_reader.py",
    "langgraph-agent/app/tools/code_executor.py",
    "langgraph-agent/app/services/vectorstore.py",
    "langgraph-agent/app/services/embeddings.py",
    "langgraph-agent/app/models/schemas.py",
    "langgraph-agent/app/config.py",
    "langgraph-agent/tests/.gitkeep",
    "langgraph-agent/Dockerfile",
    "langgraph-agent/docker-compose.yml",
    "langgraph-agent/requirements.txt",
    "langgraph-agent/.github/workflows/ci.yml",
]

def create_structure():
    for path in project_structure:
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"[DIR]  Created: {directory}")

        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write("")  # create empty file
            print(f"[FILE] Created: {path}")

if __name__ == "__main__":
    create_structure()
    print("\n✅ Project structure created successfully!")
