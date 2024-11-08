# RAG-as-Service

A robust Retrieval-Augmented Generation service that processes PDF documents and provides semantic search capabilities. Built with FastAPI, pgvector, and support for multiple embedding providers (Ollama and OpenAI).

## 🚀 Features

- **Document Processing**: Upload and process PDF, TXT, and MD files with automatic chunking
- **Text Content Upload**: Direct text content upload via API endpoint
- **Multiple Embedding Providers**: Support for both Ollama and OpenAI embeddings
- **Vector Search**: Efficient semantic search using pgvector
- **Multi-User Support**: Built-in user isolation for document management
- **Robust Error Handling**: Comprehensive error handling and logging
- **Docker Support**: Full containerization with health checks
- **API Documentation**: Auto-generated API documentation with FastAPI

## 🏗️ Architecture

### Components

- **FastAPI Application**: Main web service handling requests
- **PostgreSQL with pgvector**: Vector database for document embeddings
- **Ollama/OpenAI**: Embedding generation services
- **Docker**: Containerization and orchestration

### Directory Structure

```
.
├── app/
│   ├── api/         # API endpoints
│   ├── core/        # Core functionality
│   ├── db/          # Database models and sessions
│   ├── models/      # Pydantic models
│   ├── schemas/     # API schemas
│   └── services/    # Business logic
├── tests/           # Test suite
├── .github/         # GitHub Actions
├── logs/            # Application logs
└── docker/          # Docker configurations
```

## 🛠️ Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Make (optional, for using Makefile commands)

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/sistemica/rag-as-service.git
cd rag-as-service
```

2. Set up environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the service:
```bash
make run
```

The service will be available at http://localhost:8000

### Development Setup

1. Create virtual environment:
```bash
make dev-setup
```

2. Run tests:
```bash
make test
```

3. Run linters:
```bash
make lint
```

## 🔧 Configuration

### Environment Variables

|
 Variable 
|
 Description 
|
 Default 
|
|
----------
|
-------------
|
---------
|
|
 EMBEDDING_PROVIDER 
|
 Choose 'ollama' or 'openai' 
|
 ollama 
|
|
 EMBEDDING_MODEL 
|
 Model name for embeddings 
|
 nomic-embed-text 
|
|
 EMBEDDING_DIMENSION 
|
 Vector dimension 
|
 768 
|
|
 POSTGRES_USER 
|
 Database user 
|
 raguser 
|
|
 POSTGRES_PASSWORD 
|
 Database password 
|
 ragpass 
|
|
 POSTGRES_DB 
|
 Database name 
|
 ragdb 
|
|
 OLLAMA_BASE_URL 
|
 Ollama API URL 
|
 http://ollama:11434 
|
|
 OPENAI_API_KEY 
|
 OpenAI API key 
|
 None 
|
|
 LOG_LEVEL 
|
 Logging level 
|
 INFO 
|

## 📚 API Documentation

After starting the service, visit:
- Swagger UI: Available both at http://localhost:8000/docs and embedded in the web interface
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

#### Upload Document
```http
POST /documents/upload
Header: Collection-Name: <collection_name>
Body: form-data
  - file: PDF, TXT, or MD file

# Or for text content:
POST /documents/upload/text
Header: Collection-Name: <collection_name>
Body: JSON
{
    "name": "document_name.txt",
    "content": "Your text content here"
}
```

#### Search Documents
```http
GET /search?query=
Header: user_id: 
```

## 🚗 Deployment

### Using Docker Compose

```bash
docker-compose up -d
```

### Using GitHub Container Registry

```bash
docker pull ghcr.io/sistemica/rag-as-service:latest
```

## 🧪 Testing

Run the test suite:
```bash
make test
```

Run with coverage:
```bash
pytest --cov=app tests/
```

## 📈 Monitoring

The service includes:
- Health check endpoints
- Structured logging
- Docker health checks
- Basic metrics endpoint

## 🛡️ Security

- Non-root Docker user
- Environment variable configuration
- User isolation
- Input validation
- Error handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI framework
- pgvector extension
- Ollama project
- OpenAI

## ⚠️ Common Issues

### Known Issues

1. Large PDF files might need increased timeout settings
2. Embedding service availability affects upload speed
3. Database indexing needed for large document collections

### Troubleshooting

1. Check logs: `make logs`
2. Verify health endpoints
3. Ensure database connectivity
4. Check embedding service availability

## 📞 Support

- Create an issue in the GitHub repository
- Check existing issues for solutions
- Review the documentation

## 🗺️ Roadmap

- [ ] Batch processing for large documents
- [ ] Additional embedding providers
- [ ] Enhanced search capabilities
- [ ] User authentication
- [ ] Document sharing features
