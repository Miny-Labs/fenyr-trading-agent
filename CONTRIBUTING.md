# Contributing to Fenyr

Thank you for your interest in contributing to Fenyr! This document provides guidelines and information for contributors.

## 🌟 Ways to Contribute

- **Bug Reports**: Found a bug? Open an issue with reproduction steps
- **Feature Requests**: Have an idea? Share it in the issues
- **Code Contributions**: Submit a pull request
- **Documentation**: Help improve our docs
- **Testing**: Add test coverage

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Git
- OpenAI API access (for testing)

### Development Setup

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/fenyr-trading-agent.git
cd fenyr-trading-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available

# Create config
cp config.example.py config.py
# Edit with your test credentials
```

## 📝 Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to your branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(agent): add Bollinger Bands indicator support

- Added calculate_bollinger_bands() to TechnicalAnalysis
- Integrated with GPT tool definitions
- Updated documentation
```

## 🧪 Testing

```bash
# Run tests (when available)
pytest tests/

# Run with coverage
pytest --cov=. tests/
```

## 📐 Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Document functions with docstrings
- Keep functions focused and small

```python
def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """
    Calculate Relative Strength Index.
    
    Args:
        prices: List of closing prices
        period: RSI period (default 14)
    
    Returns:
        RSI value between 0 and 100
    """
    # Implementation
```

## 🔒 Security

- **Never** commit API keys or secrets
- Always use `config.py` (gitignored) for credentials
- Report security issues privately via email

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 💬 Questions?

Open an issue or reach out to the maintainers.

---

Thank you for contributing! 🎉
