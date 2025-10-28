CyberSecureDocAI 🛡️🤖

CyberSecureDocAI is a secure, private, and fully offline Retrieval-Augmented Generation (RAG) chatbot designed for querying your personal cybersecurity PDF documents. Built with Python, Flask, LangChain, and powered by a locally hosted Large Language Model (LLM), this application allows you to create an account, upload sensitive documents, and ask complex questions, receiving answers generated only from the content within those documents. All processing happens locally within a Docker container, ensuring your data never leaves your machine.

✨ Features

Secure User Accounts: Register and log in to keep your documents private.

Private Document Storage: Each user has their own isolated storage space for uploaded PDFs.

PDF Upload & Management: Easily upload new cybersecurity documents (PDF format) and delete old ones.

100% Offline RAG Pipeline:

Retrieval: Uses FAISS vector search to find the most relevant text chunks from your documents based on your question.

Augmentation: Inserts the retrieved context into a carefully crafted prompt.

Generation: Uses a locally hosted LLM (Qwen2-1.5B-Instruct) via llama-cpp-python to generate answers strictly based on the provided context.

Local AI Processing: All AI inference (text embedding and language generation) runs directly on your CPU within the Docker container. No external APIs or internet connection required after setup.

Containerized & Portable: Uses Docker for easy setup and consistent execution across different operating systems (Linux, macOS, Windows).

Clean Web Interface: A simple, intuitive web UI for document management and chat interaction.

🛠️ Technology Stack

Backend: Python 3.11, Flask

AI Orchestration: LangChain, LangChain Community, LangChain Hugging Face

LLM Engine: llama-cpp-python

LLM Model: Qwen/Qwen2-1.5B-Instruct-GGUF (Q4_K_M quantization)

Embedding Model: sentence-transformers/all-MiniLM-L6-v2

Vector Database: FAISS (CPU version)

PDF Parsing: pypdf

User Database: SQLite3

Containerization: Docker

Frontend: HTML, Tailwind CSS (via CDN), Vanilla JavaScript

🚀 Setup and Running

This project is designed to run within a Docker container. Ensure you have Docker installed on your system.

1. Clone the Repository (or Download Files):
Get all the project files (Dockerfile, app.py, index.html, requirements.txt) into a single directory on your machine.

2. Open Your Terminal:
Navigate into the project directory using the cd command.

cd /path/to/your/CyberSecureDocAI


3. Build the Docker Image:
This command builds the container image. This will take a significant amount of time on the first run as it needs to download base images, install dependencies, compile llama-cpp-python, and download both AI models.

docker build -t cyberdocai .


4. Run the Docker Container:
This command starts the application. It creates a ./data folder in your project directory for persistent storage (user accounts, uploaded files, vector stores) and maps the application's port 5000.

docker run --rm -it -p 5000:5000 -v ./data:/app/data cyberdocai


--rm: Automatically remove the container when you stop it (Ctrl+C).

-it: Run interactively so you can see server logs.

-p 5000:5000: Map port 5000 on your host to port 5000 in the container.

-v ./data:/app/data: Crucial! Mounts the local ./data directory into the container for persistent data storage.

5. Access the Application:
Open your web browser and navigate to:

http://localhost:5000


6. Register and Use:

You will be prompted to create an account first.

Log in with your new credentials.

Upload your cybersecurity PDF documents using the "Upload Documents" button. Processing happens automatically after upload.

Start asking questions in the chat window!

7. Stopping the Application:
Go back to the terminal where the container is running and press Control + C.

⚙️ Architecture Overview

The application follows a standard Retrieval-Augmented Generation (RAG) pattern:

Ingestion: PDFs are uploaded, text is extracted and sanitized, split into chunks, converted to embeddings using all-MiniLM-L6-v2, and stored in a user-specific FAISS vector index.

Retrieval: When a user asks a question, their query is embedded, and FAISS is searched to find the most semantically similar document chunks.

Generation: The retrieved chunks (context) and the original question are formatted into a specific prompt template and sent to the local Qwen2 LLM. The LLM generates an answer based only on this context.

⚠️ Troubleshooting

Build Failures (Network): If the docker build command fails with network errors (e.g., "TLS handshake timeout"), check your system's internet connection, DNS settings, and any potential firewall or proxy configurations that might be blocking Docker's access to the internet. Restarting the Docker service might also help.

Slow Responses: LLM inference on a CPU can be slow, especially with large contexts. Response times depend heavily on your CPU's performance. The Qwen2-1.5B model was chosen for a reasonable balance between capability and speed on typical hardware.

Permission Denied (./data folder): If you encounter permission errors when the container tries to write to the ./data volume, you might need to adjust the folder permissions on your host machine or ensure Docker has the necessary rights. On Linux, running Docker commands with sudo initially or adding your user to the docker group usually resolves this.

📄 License

(Consider adding an open-source license here, e.g., MIT or Apache 2.0)
