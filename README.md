
# 🌍 AI Translator - Multilingual Translation Web Application

A fast, AI-powered multilingual translation web application built with Django and Python. Supports 25+ languages including comprehensive African language support with Chichewa, Swahili, Yoruba, and more.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Django](https://img.shields.io/badge/Django-4.2-green)
![Languages](https://img.shields.io/badge/Languages-25%2B-orange)
![African Languages](https://img.shields.io/badge/African%20Languages-15-yellow)

## 🚀 Features

- **🌐 25+ Languages** - Comprehensive global language support
- **🇿🇦 15 African Languages** - Specialized support for African languages including Chichewa, Swahili, Yoruba, Igbo, Hausa, and more
- **🤖 AI-Powered Translation** - Uses state-of-the-art MarianMT models from HuggingFace
- **⚡ Fast Performance** - Optimized with caching and lazy loading
- **🎨 Modern UI** - Clean black and white responsive design
- **📱 Real-time Translation** - Instant results with loading indicators and error handling
- **🔧 RESTful API** - Fully functional API for integration

## 🛠️ Technology Stack

### Backend
- **Framework**: Django 4.2.7 + Django REST Framework
- **AI Models**: HuggingFace Transformers, PyTorch
- **Caching**: Django Cache Framework
- **Authentication**: Django CSRF Protection

### Frontend
- **UI Framework**: Bootstrap 5.3.0
- **Icons**: Font Awesome 6.0
- **JavaScript**: Vanilla ES6+
- **Styling**: Custom CSS with glassmorphism effects

### AI/ML
- **Translation Models**: Helsinki-NLP MarianMT models
- **Inference**: PyTorch with GPU support (if available)
- **Tokenization**: SentencePiece, Sacremoses

## 🌐 Supported Languages

### European Languages
- English (`en`), Spanish (`es`), French (`fr`), German (`de`)
- Italian (`it`), Portuguese (`pt`), Russian (`ru`)

### Asian Languages
- Chinese (`zh`), Japanese (`ja`), Korean (`ko`), Arabic (`ar`)

### African Languages
- **Swahili** (`sw`) - East Africa
- **Yoruba** (`yo`) - West Africa
- **Igbo** (`ig`) - Nigeria
- **Hausa** (`ha`) - West Africa
- **Amharic** (`am`) - Ethiopia
- **Somali** (`so`) - Horn of Africa
- **Zulu** (`zu`) - South Africa
- **Xhosa** (`xh`) - South Africa
- **Kinyarwanda** (`rw`) - Rwanda
- **Chichewa** (`ny`) - Malawi, Zambia, Zimbabwe
- **Malagasy** (`mg`) - Madagascar
- **Lingala** (`ln`) - Central Africa
- **Shona** (`sn`) - Zimbabwe
- **Sesotho** (`st`) - Lesotho
- **Setswana** (`tn`) - Botswana

## 📦 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git

### Step-by-Step Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-translator.git
   cd ai-translator
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv translator_env
   translator_env\Scripts\activate
   
   # macOS/Linux
   python3 -m venv translator_env
   source translator_env/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file in project root
   echo "SECRET_KEY=your-secret-key-here" > .env
   echo "DEBUG=True" >> .env
   ```

5. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   ```
   Open http://127.0.0.1:8000/ in your browser
   ```

## 🎯 Usage

### Web Interface
1. **Access the translator** at `http://127.0.0.1:8000/`
2. **Select languages** from the organized dropdown menus (grouped by region)
3. **Enter text** in the input area (maximum 1000 characters)
4. **Click "Translate"** or press `Ctrl + Enter` for quick translation
5. **View results** in the output area with translation timing

### API Endpoints

The application provides RESTful API endpoints:

- **POST** `/api/translate/` - Translate text
  ```json
  {
    "text": "Hello, how are you?",
    "source_lang": "en",
    "target_lang": "sw"
  }
  ```

- **GET** `/api/languages/` - Get supported languages list

- **GET** `/api/health/` - Health check endpoint

### Example API Usage
```bash
curl -X POST http://127.0.0.1:8000/api/translate/ \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?",
    "source_lang": "en",
    "target_lang": "ny"
  }'
```

## 📁 Project Structure

```
ai-translator/
├── ai_translator/                 # Django project configuration
│   ├── settings.py               # Project settings
│   ├── urls.py                   # Main URL routing
│   └── wsgi.py                   # WSGI configuration
├── translator/                    # Main application
│   ├── services/
│   │   └── translation_service.py # AI translation service
│   ├── templates/
│   │   └── translator/
│   │       └── index.html        # Main UI template
│   ├── static/                   # Static files (CSS, JS)
│   ├── views.py                  # API and view handlers
│   ├── urls.py                   # App URL routing
│   └── apps.py                   # App configuration
├── manage.py                     # Django management script
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables
├── .gitignore                    # Git ignore rules
└── README.md                     # Project documentation
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:
```env
SECRET_KEY=your-django-secret-key
DEBUG=True
```

### Cache Configuration
The application uses Django's cache framework for:
- Translation result caching (5 minutes)
- Model loading optimization
- Performance improvement

## 🚀 Deployment

### For Production
1. Set `DEBUG=False` in environment variables
2. Generate a secure secret key
3. Configure proper database (PostgreSQL recommended)
4. Set up Redis for caching
5. Use production WSGI server (Gunicorn)
6. Configure web server (Nginx/Apache)
7. Set up SSL certificate

### Example Production Settings
```python
# In settings.py
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

## 🤝 Contributing

We welcome contributions! Please feel free to submit issues and pull requests.

### Development Setup
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Areas for Contribution
- Adding more language pairs
- Improving translation quality
- Enhancing UI/UX
- Adding voice translation
- Mobile app development

## 📊 Performance Notes

- **First Translation**: May take 10-30 seconds as models download
- **Subsequent Translations**: Typically under 1 second due to caching
- **Memory Usage**: Models are loaded on-demand and shared between requests
- **Concurrent Users**: Limited by available RAM and model sizes

## 🐛 Troubleshooting

### Common Issues

1. **NumPy Compatibility Warnings**
   ```bash
   pip uninstall numpy -y
   pip install numpy==1.24.3
   ```

2. **Model Download Failures**
   - Check internet connection
   - Verify HuggingFace access
   - Clear cache: `rm -rf ~/.cache/huggingface`

3. **Memory Issues**
   - Use smaller models
   - Implement model offloading
   - Increase swap space

4. **Translation Errors**
   - Check language pair support
   - Verify text length limits
   - Review server logs

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [HuggingFace](https://huggingface.co/) for providing state-of-the-art NLP models
- [Helsinki-NLP](https://github.com/Helsinki-NLP) for the MarianMT translation models
- [Django Software Foundation](https://www.djangoproject.com/) for the excellent web framework
- [Bootstrap](https://getbootstrap.com/) for the responsive UI components
- [Font Awesome](https://fontawesome.com/) for the beautiful icons

## 📞 Support

If you encounter any issues or have questions:

1. Check the Issues page on GitHub
2. Create a new issue with detailed description
3. Provide your environment details and error logs

