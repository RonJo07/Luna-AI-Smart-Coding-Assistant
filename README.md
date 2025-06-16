# Luna AI - Smart Coding Assistant

A powerful local AI coding assistant powered by Phi-4 model, built with FastAPI and modern web technologies. This application provides intelligent code assistance, debugging help, and coding suggestions without requiring an internet connection.

## Features

- 🚀 Local AI processing - no internet required
- 💻 Web-based coding interface
- 🔒 Privacy-focused - all code stays on your machine
- ⚡ Fast response times
- 📊 Performance monitoring
- 🎯 Memory-efficient configuration
- 🛠️ Smart code suggestions and debugging
- 📝 Code explanation and documentation
- 🔍 Intelligent error analysis

## Prerequisites

- Python 3.8 or higher
- 16GB RAM minimum 
- Windows 10/11 or Linux
- C++ Build Tools (Windows only): [MS Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- CMake (https://cmake.org/) – required for building llama-cpp-python
- (Optional) Ninja or Meson – alternative build systems
- Git: https://git-scm.com/download/win
- llama.cpp: https://github.com/ggerganov/llama.cpp
- llama-cpp-python: https://pypi.org/project/llama-cpp-python/

## Installation

1. Clone the repository:
```bash
git clone https://github.com/RonJo07/Luna-AI-Smart-Coding-Assistant.git

```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download the model:
   - Create a `backend/model` directory
   - Download the Phi-4 model (Q3_K_S quantized version) and place it in the `backend/model` directory
      https://huggingface.co/microsoft/phi-4-gguf/resolve/main/phi-4-Q3_K_S.gguf
   - Rename it to `phi-4-Q3_K_S.gguf`

## Running the Application

1. Start the server:
```bash
python backend/main.py
```

2. Open your web browser and navigate to:
```
http://localhost:8000
```

3. Configure the model:
   - When prompted, enter the path to your model file
   - The default path is `backend/model/phi-4-Q3_K_S.gguf`
   - Click "Configure" to start using the AI

## Project Structure

```
luna-ai/
├── backend/
│   ├── main.py           # FastAPI server
│   └── model/            # Model directory
├── frontend/
│   ├── index.html        # Main interface
│   ├── styles.css        # Styling
│   └── script.js         # Frontend logic
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Configuration

The application automatically creates a configuration file in your home directory:
- Windows: `%USERPROFILE%\.luna-ai\config.json`
- Linux/Mac: `~/.luna-ai/config.json`

## Performance Tuning

The application automatically optimizes for your system's resources:
- Adjusts context window based on available memory
- Optimizes thread count for your CPU
- Uses memory-efficient settings

## Troubleshooting

1. **Model Loading Error**
   - Ensure you have enough RAM (8GB minimum)
   - Check if the model file exists in the correct location
   - Verify the model file is not corrupted

2. **Configuration Error**
   - Delete the `.luna-ai` folder in your home directory
   - Restart the application
   - Reconfigure the model

3. **Memory Issues**
   - Close other applications
   - Use a smaller model version
   - Adjust the context window size

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [llama.cpp](https://github.com/ggerganov/llama.cpp) for the model implementation
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Phi-4](https://huggingface.co/microsoft/phi-4) for the AI model 
