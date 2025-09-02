# Contributing to InLegalDesk

Thank you for your interest in contributing to InLegalDesk! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic understanding of legal systems (preferred)
- Familiarity with AI/ML concepts (helpful)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/inlegaldesk.git
   cd inlegaldesk
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r desktop/requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Setup Environment**
   ```bash
   cp .env.sample .env
   # Edit .env with your configuration
   ```

## 📋 Types of Contributions

### 🐛 Bug Reports

When reporting bugs, please include:

- **Clear description** of the issue
- **Steps to reproduce** the problem
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Screenshots** (if applicable)
- **Error logs** (if available)

### ✨ Feature Requests

For new features, please provide:

- **Clear description** of the proposed feature
- **Use case** and motivation
- **Proposed implementation** (if you have ideas)
- **Alternative solutions** considered

### 🔧 Code Contributions

We welcome code contributions in the following areas:

- **Backend improvements** (FastAPI, document processing)
- **Frontend enhancements** (PySide6 GUI)
- **AI/ML models** (vision-language, embeddings)
- **Legal domain knowledge** (Indian law, precedents)
- **Testing and documentation**
- **Performance optimizations**

## 🛠️ Development Guidelines

### Code Style

- **Python**: Follow PEP 8
- **Type hints**: Use type annotations
- **Docstrings**: Document all functions and classes
- **Comments**: Explain complex logic

```python
def process_legal_document(
    document_path: str, 
    language: str = "en"
) -> Dict[str, Any]:
    """
    Process a legal document for ingestion.
    
    Args:
        document_path: Path to the document file
        language: Language of the document (en/hi)
        
    Returns:
        Dictionary containing processed document data
        
    Raises:
        FileNotFoundError: If document file doesn't exist
        ValueError: If language is not supported
    """
    # Implementation here
    pass
```

### Git Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run unit tests
   pytest tests/
   
   # Run E2E tests
   python run_e2e.py
   
   # Check code style
   black .
   flake8 .
   mypy .
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new legal document processor"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format

Use conventional commits:

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

Examples:
```
feat: add support for Tamil language documents
fix: resolve PDF rendering issue on Windows
docs: update API documentation
test: add unit tests for document chunking
```

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_ingest.py

# Run with coverage
pytest --cov=. --cov-report=html
```

### Integration Tests

```bash
# Run E2E tests
python run_e2e.py

# Run with specific backend URL
python run_e2e.py --backend-url http://localhost:8000
```

### Manual Testing

1. **Backend Testing**
   ```bash
   # Start backend
   python -m uvicorn app:app --reload
   
   # Test endpoints
   curl http://localhost:8877/health
   ```

2. **Desktop App Testing**
   ```bash
   cd desktop
   python main.py
   ```

## 📚 Documentation

### Code Documentation

- Use docstrings for all public functions/classes
- Include type hints
- Add inline comments for complex logic
- Update README.md for new features

### API Documentation

- Update OpenAPI schemas in FastAPI
- Add examples for new endpoints
- Document error responses

### User Documentation

- Update README.md for new features
- Add usage examples
- Update installation instructions

## 🏗️ Architecture Guidelines

### Backend (FastAPI)

- **Modular design**: Separate concerns into modules
- **Async/await**: Use async functions for I/O operations
- **Error handling**: Proper exception handling and logging
- **Validation**: Use Pydantic models for request/response validation

### Frontend (PySide6)

- **MVC pattern**: Separate UI, logic, and data
- **Responsive design**: Handle different screen sizes
- **Error handling**: User-friendly error messages
- **Accessibility**: Follow accessibility guidelines

### AI/ML Components

- **Model abstraction**: Use base classes for different models
- **Configuration**: Make models configurable
- **Fallback mechanisms**: Handle model failures gracefully
- **Performance**: Optimize for speed and memory usage

## 🔍 Code Review Process

### For Contributors

1. **Self-review**: Review your own code before submitting
2. **Test thoroughly**: Ensure all tests pass
3. **Document changes**: Update relevant documentation
4. **Be responsive**: Address review feedback promptly

### For Reviewers

1. **Be constructive**: Provide helpful feedback
2. **Check functionality**: Ensure code works as intended
3. **Verify tests**: Ensure adequate test coverage
4. **Consider security**: Look for potential security issues

## 🐛 Issue Templates

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
 - OS: [e.g. Windows 10]
 - Python version: [e.g. 3.9.0]
 - InLegalDesk version: [e.g. 1.0.0]

**Additional context**
Any other context about the problem.
```

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
A clear description of any alternative solutions.

**Additional context**
Any other context or screenshots about the feature request.
```

## 📞 Getting Help

### Communication Channels

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: dev@inlegaldesk.com for private matters

### Response Times

- **Bug reports**: Within 48 hours
- **Feature requests**: Within 1 week
- **Pull requests**: Within 3-5 business days
- **General questions**: Within 1 week

## 🏆 Recognition

Contributors will be recognized in:

- **README.md**: Listed as contributors
- **Release notes**: Mentioned for significant contributions
- **GitHub**: Added to contributors list

## 📋 Checklist for Pull Requests

Before submitting a PR, ensure:

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] PR description is detailed
- [ ] No merge conflicts
- [ ] Branch is up to date

## 🚫 What Not to Contribute

Please avoid:

- **Breaking changes** without discussion
- **Code without tests**
- **Undocumented code**
- **Security vulnerabilities**
- **Copyright violations**
- **Spam or off-topic content**

## 📄 Legal

By contributing to InLegalDesk, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to InLegalDesk! Your efforts help make legal research more accessible and efficient.