import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import shutil

# Suppress noisy TensorFlow logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Attempt to import langchain components, handling potential import errors
try:
    from langchain_community.document_loaders import PyPDFLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings
except ImportError:
    print("LangChain components not found. Please install them with 'pip install -r requirements.txt'")
    exit()

# --- Configuration ---
UPLOAD_FOLDER = 'uploads'
VECTOR_STORE_PATH = 'faiss_index'
ALLOWED_EXTENSIONS = {'pdf'}

# --- Flask App Initialization ---
app = Flask(__name__, template_folder='.')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Global Variables ---
vector_store = None
embeddings = None

# --- Helper Functions ---
def allowed_file(filename):
    """Checks if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def initialize_rag_components():
    """Initializes the embedding model and loads the vector store if it exists."""
    global embeddings, vector_store

    # Initialize the embedding model
    print("Initializing embedding model...")
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': False}
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )
    print("Embedding model initialized.")

    # Load the vector store if it exists
    if os.path.exists(VECTOR_STORE_PATH):
        print(f"Loading existing vector store from '{VECTOR_STORE_PATH}'...")
        try:
            vector_store = FAISS.load_local(VECTOR_STORE_PATH, embeddings, allow_dangerous_deserialization=True)
            print("Vector store loaded successfully.")
        except Exception as e:
            print(f"Error loading vector store: {e}. A new one will be created upon file upload.")
            vector_store = None
    else:
        print("No existing vector store found. A new one will be created.")
        vector_store = None

def process_and_add_document(file_path):
    """Loads, splits, and adds a document to the vector store."""
    global vector_store
    print(f"Processing document: {file_path}")
    try:
        # Load the document
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        # Split the document into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        texts = text_splitter.split_documents(documents)

        if not texts:
            print(f"Warning: No text could be extracted from {os.path.basename(file_path)}")
            return

        # Add the document chunks to the vector store
        if vector_store is None:
            # Create a new vector store if it doesn't exist
            print("Creating new vector store...")
            vector_store = FAISS.from_documents(texts, embeddings)
        else:
            # Add to the existing vector store
            print("Adding documents to existing vector store...")
            vector_store.add_documents(texts)

        # Save the updated vector store
        vector_store.save_local(VECTOR_STORE_PATH)
        print(f"Successfully processed and added {os.path.basename(file_path)} to the vector store.")

    except Exception as e:
        print(f"Failed to process {os.path.basename(file_path)}. Error: {e}")

def rebuild_vector_store():
    """Rebuilds the entire vector store from documents in the upload folder."""
    global vector_store
    print("Rebuilding vector store...")

    # Remove the old index
    if os.path.exists(VECTOR_STORE_PATH):
        shutil.rmtree(VECTOR_STORE_PATH)

    vector_store = None

    # Process all existing documents
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    if not files:
        print("No files to process. Vector store is empty.")
        return

    for filename in files:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.isfile(file_path) and allowed_file(filename):
            process_and_add_document(file_path)

    print("Vector store rebuilt successfully.")


# --- Flask Routes ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handles file uploads."""
    if 'files' not in request.files:
        return jsonify({'success': False, 'message': 'No files part in the request'}), 400

    files = request.files.getlist('files')
    files_processed = 0

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            if os.path.exists(file_path):
                print(f"Skipping already uploaded file: {filename}")
                continue

            file.save(file_path)
            process_and_add_document(file_path)
            files_processed += 1

    if files_processed > 0:
        return jsonify({'success': True, 'message': f'Successfully uploaded and processed {files_processed} new file(s).'})
    else:
        return jsonify({'success': True, 'message': 'No new files to upload.'})


@app.route('/documents', methods=['GET'])
def get_documents():
    """Returns a list of uploaded documents."""
    try:
        documents = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f))]
        return jsonify({'documents': documents})
    except FileNotFoundError:
        return jsonify({'documents': []})


@app.route('/delete/<filename>', methods=['DELETE'])
def delete_document(filename):
    """Deletes a document and rebuilds the vector store."""
    try:
        filename = secure_filename(filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            rebuild_vector_store()
            return jsonify({'success': True, 'message': f'{filename} deleted successfully.'})
        else:
            return jsonify({'success': False, 'message': 'File not found.'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/chat', methods=['POST'])
def chat():
    """Handles chat queries."""
    data = request.json
    message = data.get('message')

    if not message:
        return jsonify({'reply': 'No message received.'}), 400

    if vector_store is None:
        return jsonify({'reply': 'I am ready to help! Please upload some documents first so I can answer your questions.'})

    try:
        # Retrieve relevant documents from the vector store
        print(f"Searching for relevant context for query: '{message}'")
        retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})
        relevant_docs = retriever.invoke(message)

        if not relevant_docs:
            return jsonify({'reply': "I couldn't find any relevant information in the uploaded documents to answer your question. Please try asking something else."})

        context = "\n".join([doc.page_content for doc in relevant_docs])

        # --- LLM Integration Placeholder ---
        # In a real application, you would pass the context and message to a language model.
        # Here, we simulate a response for demonstration purposes.

        prompt = f"""
        Based on the following information from your documents:
        ---
        {context}
        ---
        Please answer the question: {message}
        """

        # Simulated LLM response
        simulated_reply = (
            f"Based on the provided documents, here is the information related to your question:\n\n"
            f"{context}\n\n"
            f"--- \n*Disclaimer: This is a simulated response. The context above was retrieved from your documents as being the most relevant to your query.*"
        )
        print("Generated a simulated reply.")

        return jsonify({'reply': simulated_reply})

    except Exception as e:
        print(f"Error during chat processing: {e}")
        return jsonify({'reply': 'An error occurred while processing your request.'}), 500


# --- Main Execution ---
if __name__ == '__main__':
    # Create necessary directories
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # Initialize RAG components on startup
    initialize_rag_components()

    # Start the Flask app
    app.run(debug=True, port=5000)
