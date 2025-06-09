from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
import json
import time
import psutil
import multiprocessing
from pathlib import Path
from llama_cpp import Llama
import logging
import uvicorn
from datetime import datetime

# Set up logging
LOG_DIR = Path.home() / ".luna-ai" / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"luna_ai_{datetime.now().strftime('%Y%m%d')}.log"

# Configure logging
logger = logging.getLogger("luna_ai")
logger.setLevel(logging.INFO)

# Create handlers
file_handler = logging.FileHandler(LOG_FILE)
console_handler = logging.StreamHandler()

# Create formatters and add it to handlers
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(log_format)
console_handler.setFormatter(log_format)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Define Pydantic models first
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str

class ModelConfig(BaseModel):
    model_path: str

class ConfigRequest(BaseModel):
    model_path: str
    model_config: Optional[dict] = None

class ConfigResponse(BaseModel):
    model_path: str
    model_config: dict
    status: str

# Initialize FastAPI app
app = FastAPI(title="Luna AI")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add DLL directory to path if running as frozen executable
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle
    BASE_DIR = Path(sys._MEIPASS)
    os.environ['PATH'] = str(BASE_DIR / 'llama_cpp') + os.pathsep + os.environ['PATH']
else:
    # If the application is run from a Python interpreter
    BASE_DIR = Path(__file__).parent.parent

# Mount static files with explicit HTML configuration
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "frontend"), html=True), name="static")

# Configuration
CONFIG_DIR = Path.home() / ".luna-ai"
CONFIG_FILE = CONFIG_DIR / "config.json"
MODEL_DIR = Path(__file__).parent / "model"  # Use the model directory in the backend folder

# Ensure directories exist
CONFIG_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

# Initialize model as None
model = None

# Performance monitoring
class PerformanceMetrics:
    def __init__(self):
        self.total_tokens = 0
        self.total_time = 0
        self.requests = 0
    
    def add_request(self, tokens, time_taken):
        self.total_tokens += tokens
        self.total_time += time_taken
        self.requests += 1
        # Log performance metrics
        logger.info(f"Performance - Tokens: {tokens}, Time: {time_taken:.2f}s, Speed: {tokens/time_taken:.2f} tokens/s")
    
    def get_average_speed(self):
        if self.total_time == 0:
            return 0
        return self.total_tokens / self.total_time

metrics = PerformanceMetrics()

def get_system_info():
    cpu_count = multiprocessing.cpu_count()
    memory = psutil.virtual_memory()
    system_info = {
        "cpu_count": cpu_count,
        "total_memory": memory.total,
        "available_memory": memory.available
    }
    logger.info(f"System Info - CPU Cores: {cpu_count}, Total Memory: {memory.total/1024/1024/1024:.1f}GB, Available Memory: {memory.available/1024/1024/1024:.1f}GB")
    return system_info

def optimize_model_config():
    system_info = get_system_info()
    cpu_count = system_info["cpu_count"]
    available_memory = system_info["available_memory"]
    
    # Calculate optimal thread count (use only 25% of available cores to minimize memory usage)
    n_threads = max(1, int(cpu_count * 0.25))
    
    # Calculate context size based on available memory
    # Using an extremely conservative estimate: 0.5GB per 512 tokens
    max_context = min(512, int((available_memory * 0.2) / (512 * 1024 * 1024) * 512))
    
    config = {
        "n_ctx": max_context,
        "n_threads": n_threads,
        "n_batch": 128,  # Minimal batch size
        "n_gpu_layers": 0,  # CPU only for now
        "f16_kv": True,  # Use half-precision for key/value cache
        "embedding": False,  # Disable embedding layer to save memory
        "rope_scaling": None,  # Disable RoPE scaling to save memory
        "use_mlock": False,  # Disable memory locking
        "use_mmap": True,  # Use memory mapping
        "n_gqa": 1,  # Minimal group attention
        "rms_norm_eps": 1e-6,  # Minimal normalization epsilon
        "vocab_only": False,  # Don't load vocabulary only
        "use_mmap": True,  # Use memory mapping
        "use_mlock": False,  # Don't lock memory
        "tensor_split": None,  # Don't split tensors
        "seed": 42,  # Fixed seed for reproducibility
        "verbose": False  # Disable verbose output
    }
    logger.info(f"Ultra Memory-efficient Model Config - Context: {max_context}, Threads: {n_threads}, Batch: 128")
    return config

def load_model(model_path: str):
    global model
    try:
        config = optimize_model_config()
        logger.info(f"Loading model from: {model_path}")
        logger.info(f"Model configuration: {config}")
        
        # Verify file exists and is readable
        if not os.path.exists(model_path):
            logger.error(f"Model file does not exist: {model_path}")
            return False
            
        # Check file size
        file_size = os.path.getsize(model_path) / (1024 * 1024 * 1024)  # Convert to GB
        logger.info(f"Model file size: {file_size:.2f} GB")
        
        # Check available memory
        available_memory = psutil.virtual_memory().available / (1024 * 1024 * 1024)  # Convert to GB
        logger.info(f"Available system memory: {available_memory:.2f} GB")
        
        # Ultra conservative memory requirement (1.1x model size)
        if available_memory < file_size * 1.1:
            logger.error(f"Insufficient memory to load model. Need at least {file_size * 1.1:.2f} GB, but only have {available_memory:.2f} GB available")
            return False
        
        try:
            # Try to load the model with minimal configuration first
            logger.info("Attempting to load model with minimal configuration...")
            model = Llama(
                model_path=model_path,
                n_ctx=256,  # Start with a tiny context
                n_threads=1,  # Use single thread initially
                n_batch=64,  # Minimal batch size
                f16_kv=True,
                embedding=False,
                use_mmap=True,
                use_mlock=False
            )
            logger.info("Model loaded successfully with minimal configuration")
            
            # Now try to load with optimized configuration
            logger.info("Reloading model with optimized configuration...")
            model = Llama(
                model_path=model_path,
                **config
            )
            logger.info("Model loaded successfully with optimized configuration")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing Llama model: {str(e)}")
            logger.error("This might be due to:")
            logger.error("1. Incompatible model format")
            logger.error("2. Corrupted model file")
            logger.error("3. Insufficient system resources")
            logger.error("4. Incompatible model version")
            return False
            
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        return False

def save_config(config: ModelConfig):
    try:
        # Convert path to absolute path and normalize
        model_path = str(Path(config.model_path).resolve())
        config_dict = config.dict()
        config_dict['model_path'] = model_path
        
        # Ensure config directory exists
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_dict, f)
        logger.info(f"Configuration saved: {config_dict}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")
        return False

def get_default_model_path():
    """Get the default model path"""
    model_path = MODEL_DIR / "phi-4-Q3_K_S.gguf"
    if model_path.exists():
        return str(model_path.resolve())
    return None

def load_config():
    global model
    config = {"model_path": "", "model_config": {}}
    
    # Try to load from saved config first
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from file: {config}")
        except Exception as e:
            logger.error(f"Error loading configuration from file: {str(e)}")

    # If no model path in config or it doesn't exist, try default model in backend/model
    model_path_from_config = config.get('model_path')
    if not model_path_from_config or not Path(model_path_from_config).exists():
        default_model_in_dir = MODEL_DIR / "phi-4-Q3_K_S.gguf"
        if default_model_in_dir.exists():
            logger.info(f"Default model found in backend/model: {default_model_in_dir}")
            config['model_path'] = str(default_model_in_dir.resolve())
        else:
            logger.info("No saved model path found and no default model in backend/model.")

    # Attempt to load the model if a path is available
    if config['model_path']:
        logger.info(f"Attempting to load model from path: {config['model_path']}")
        if load_model(config['model_path']):
            logger.info("Model auto-loaded successfully.")
        else:
            logger.error("Model auto-load failed. Configuration will be required.")
            config['model_loaded'] = False # Indicate that model loading failed
    else:
        logger.info("No model path available to load.")
        config['model_loaded'] = False # Indicate that no model was loaded

    return config

@app.get("/")
async def read_root():
    return FileResponse(str(BASE_DIR / "frontend" / "index.html"))

@app.get("/api/model/status")
async def get_model_status():
    global model
    current_config = load_config() # Reload config to get latest status
    
    is_model_loaded = model is not None
    model_path = current_config.get('model_path', 'Not Configured')

    status_message = "Model loaded successfully." if is_model_loaded else "Model not loaded." 
    if not is_model_loaded and not current_config.get('model_path'):
        status_message = "Model not configured. Please provide a model path."
    elif not is_model_loaded and current_config.get('model_path') and not Path(current_config.get('model_path')).exists():
        status_message = f"Model file not found at configured path: {current_config.get('model_path')}."
    elif not is_model_loaded and current_config.get('model_path') and Path(current_config.get('model_path')).exists():
        status_message = f"Model failed to load from path: {current_config.get('model_path')}. Please check logs."

    return {
        "model_loaded": is_model_loaded,
        "model_path": model_path,
        "status": status_message
    }

@app.post("/api/model/configure")
async def configure_model(config: ModelConfig):
    if not config.model_path:
        logger.error("Model path is empty")
        raise HTTPException(status_code=400, detail="Model path cannot be empty")
    
    # Convert to Path object and resolve
    model_path = Path(config.model_path).resolve()
    
    if not model_path.exists():
        logger.error(f"Model file not found: {model_path}")
        raise HTTPException(status_code=400, detail=f"Model file not found at: {model_path}")
    
    try:
        if load_model(str(model_path)):
            if save_config(config):
                logger.info("Model configured successfully")
                return {"status": "success"}
            else:
                logger.error("Failed to save configuration")
                raise HTTPException(status_code=500, detail="Failed to save configuration")
        else:
            logger.error("Failed to load model")
            raise HTTPException(status_code=500, detail="Failed to load model. Check server logs for details.")
    except Exception as e:
        logger.error(f"Error during model configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during model configuration: {str(e)}")

@app.post("/api/chat")
async def chat(request: ChatRequest):
    if model is None:
        config = load_config()
        if not config or not load_model(config['model_path']):
            logger.error("Model not loaded for chat request")
            raise HTTPException(status_code=400, detail="Model not loaded")
    
    try:
        logger.info(f"Processing chat request: {request.message[:100]}...")
        start_time = time.time()
        response = model.create_completion(
            request.message,
            max_tokens=512,
            temperature=0.7,
            stop=["User:", "\n\n"]
        )
        end_time = time.time()
        
        # Calculate performance metrics
        tokens = len(response['choices'][0]['text'].split())
        time_taken = end_time - start_time
        metrics.add_request(tokens, time_taken)
        
        result = {
            "response": response['choices'][0]['text'],
            "performance": {
                "tokens": tokens,
                "time_taken": time_taken,
                "tokens_per_second": tokens / time_taken if time_taken > 0 else 0
            }
        }
        logger.info(f"Chat response generated - Tokens: {tokens}, Time: {time_taken:.2f}s")
        return result
    except Exception as e:
        logger.error(f"Error in chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info("Starting Luna AI server")
    
    # Try to load model from config if it exists
    config = load_config()
    if config and config.get('model_path') and os.path.exists(config['model_path']):
        logger.info(f"Attempting to load model from config: {config['model_path']}")
        load_model(config['model_path'])
    else:
        logger.info("No valid model configuration found")
    
    # Start the server with custom logging configuration
    logger.info("Server starting on http://127.0.0.1:8000")
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8000,
        log_config=None  # Disable uvicorn's default logging
    ) 