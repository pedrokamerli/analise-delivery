# Reaproveita a imagem do outro dashboard da VPS: Python, Pandas e Streamlit
# já estão instalados nela. Assim, esta imagem adiciona apenas o Plotly.
FROM observatorio-municipios-observatorio-municipios:latest

WORKDIR /app

RUN pip install --no-cache-dir "plotly>=5.24,<6"

# Somente o dashboard e agregações sem dados identificáveis entram na imagem.
COPY dashboard ./dashboard
COPY dados/publicos ./dados/publicos

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
