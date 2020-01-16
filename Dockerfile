FROM python:3.7-slim
ADD VERSION .

WORKDIR /usr/src/app

# Python modules
COPY requirements.txt ./
RUN \
  pip3 install --upgrade setuptools && \
  pip3 install --no-cache-dir -r requirements.txt

# App
COPY app/ ./

CMD [ "python", "app.py", "--log-level", "debug"]