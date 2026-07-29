FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libsndfile1 libgomp1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "from funasr import AutoModel; AutoModel(model='iic/SenseVoiceSmall', vad_model='fsmn-vad', punc_model='ct-punc-c', device='cpu', disable_pbar=True, disable_log=True)" || echo "skip"

COPY backend/ .

RUN mkdir -p /data/uploads
ENV UPLOAD_DIR=/data/uploads
ENV PORT=7860
EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
